"""Image normalisation and preprocessing variants for OCR.

The goal is to give the recognition engines several *good* views of the same
page instead of one raw photo: upright, deskewed, shadow-free, denoised,
denoised+binary and sharpened. A later stage picks the best reading.
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageOps

try:  # OpenCV is optional at runtime, same contract as the rest of the app.
    import cv2
except Exception:  # noqa: BLE001
    cv2 = None


MIN_SIDE = 1500
MAX_SIDE = 3200


@dataclass
class Variant:
    name: str
    image: np.ndarray  # uint8 grayscale
    kind: str  # "gray" | "binary"


def load_image(data: bytes) -> Image.Image:
    """Open, orient and flatten an uploaded image."""
    img = Image.open(io.BytesIO(data))
    img = ImageOps.exif_transpose(img)
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        background = Image.new("RGB", rgba.size, (255, 255, 255))
        background.paste(rgba, mask=rgba.split()[-1])
        img = background
    return img.convert("RGB")


def normalize_scale(
    img: Image.Image, min_side: int = MIN_SIDE, max_side: int = MAX_SIDE
) -> Image.Image:
    """Upscale small photos, cap huge ones. Never squash the aspect ratio."""
    w, h = img.size
    if not w or not h:
        return img
    longest = max(w, h)
    if longest < min_side:
        scale = min(min_side / float(longest), 4.0)
    elif longest > max_side:
        scale = max_side / float(longest)
    else:
        scale = 1.0
    if abs(scale - 1.0) < 0.01:
        return img
    size = (max(1, round(w * scale)), max(1, round(h * scale)))
    return img.resize(size, Image.LANCZOS)


def _to_gray(img: Image.Image) -> np.ndarray:
    return np.array(img.convert("L"))


def _maybe_invert(gray: np.ndarray) -> np.ndarray:
    """White text on a dark board is a common photo; normalise to dark-on-light."""
    if gray.size and float(np.mean(gray)) < 90.0:
        return 255 - gray
    return gray


def _deskew(gray: np.ndarray) -> np.ndarray:
    if cv2 is None or gray.size == 0:
        return gray
    h, w = gray.shape[:2]
    scale = 900.0 / max(h, w) if max(h, w) > 900 else 1.0
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    try:
        binary = cv2.threshold(
            small, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )[1]
        coords = np.column_stack(np.where(binary > 0))
        if len(coords) < 80:
            return gray
        angle = cv2.minAreaRect(coords)[-1]
        # OpenCV returns the angle in [-90, 0); convert to a small rotation.
        angle = -(90 + angle) if angle < -45 else -angle
        if abs(angle) < 0.35 or abs(angle) > 12.0:
            return gray
        matrix = cv2.getRotationMatrix2D((w / 2.0, h / 2.0), angle, 1.0)
        return cv2.warpAffine(
            gray,
            matrix,
            (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_CONSTANT,
            borderValue=255,
        )
    except Exception:  # noqa: BLE001
        return gray


def _order_points(points: np.ndarray) -> np.ndarray:
    rect = np.zeros((4, 2), dtype="float32")
    sums = points.sum(axis=1)
    rect[0] = points[np.argmin(sums)]
    rect[2] = points[np.argmax(sums)]
    diffs = np.diff(points, axis=1)
    rect[1] = points[np.argmin(diffs)]
    rect[3] = points[np.argmax(diffs)]
    return rect


def _perspective(gray: np.ndarray) -> np.ndarray:
    """Rectify a photographed page when a clean quadrilateral is found."""
    if cv2 is None or gray.size == 0:
        return gray
    h, w = gray.shape[:2]
    if min(h, w) < 240:
        return gray
    scale = 1000.0 / max(h, w) if max(h, w) > 1000 else 1.0
    small = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
    try:
        blurred = cv2.GaussianBlur(small, (5, 5), 0)
        edges = cv2.Canny(blurred, 40, 140)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
        contours, _ = cv2.findContours(
            edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )
        if not contours:
            return gray
        contour = max(contours, key=cv2.contourArea)
        if cv2.contourArea(contour) < 0.22 * small.shape[0] * small.shape[1]:
            return gray
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.02 * perimeter, True)
        if len(approx) != 4:
            return gray
        points = approx.reshape(4, 2).astype("float32") / scale
        rect = _order_points(points)
        tl, tr, br, bl = rect
        width = max(np.linalg.norm(br - bl), np.linalg.norm(tr - tl))
        height = max(np.linalg.norm(tr - br), np.linalg.norm(tl - bl))
        if width < 160 or height < 60:
            return gray
        destination = np.array(
            [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
            dtype="float32",
        )
        matrix = cv2.getPerspectiveTransform(rect, destination)
        warped = cv2.warpPerspective(
            gray,
            matrix,
            (int(width), int(height)),
            flags=cv2.INTER_CUBIC,
            borderValue=255,
        )
        return warped
    except Exception:  # noqa: BLE001
        return gray


def _illumination_normalize(gray: np.ndarray) -> np.ndarray:
    """Remove shadows / uneven phone lighting by dividing out the background."""
    if cv2 is None or gray.size == 0:
        return gray
    h, w = gray.shape[:2]
    sigma = max(12.0, min(h, w) / 28.0)
    background = cv2.GaussianBlur(gray, (0, 0), sigma)
    normalized = cv2.divide(gray, background, scale=255)
    return cv2.normalize(normalized, None, 0, 255, cv2.NORM_MINMAX)


def _clahe(gray: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return gray
    try:
        return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(gray)
    except Exception:  # noqa: BLE001
        return gray


def _sharpen(gray: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return gray
    blurred = cv2.GaussianBlur(gray, (0, 0), 1.0)
    return cv2.addWeighted(gray, 1.55, blurred, -0.55, 0)


def _adaptive(gray: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return gray
    h, w = gray.shape[:2]
    block = max(25, min(75, (min(h, w) // 18) | 1))
    if block % 2 == 0:
        block += 1
    return cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        block,
        11,
    )


def _otsu(gray: np.ndarray) -> np.ndarray:
    if cv2 is None:
        return gray
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)
    return cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]


def _sauvola(gray: np.ndarray) -> Optional[np.ndarray]:
    try:
        from skimage.filters import threshold_sauvola

        window = max(15, min(101, (min(gray.shape[:2]) // 8) | 1))
        threshold = threshold_sauvola(gray, window_size=window, k=0.25)
        return (gray > threshold).astype(np.uint8) * 255
    except Exception:  # noqa: BLE001
        return None


def _border(gray: np.ndarray, pixels: int = 24) -> np.ndarray:
    if cv2 is None:
        return gray
    return cv2.copyMakeBorder(
        gray, pixels, pixels, pixels, pixels, cv2.BORDER_CONSTANT, value=255
    )


def _prepare_gray(img: Image.Image) -> np.ndarray:
    gray = _to_gray(normalize_scale(img))
    gray = _maybe_invert(gray)
    gray = _perspective(gray)
    gray = _deskew(gray)
    return gray


def build_variants(img: Image.Image, thorough: bool = True) -> List[Variant]:
    """Return recognition-ready grayscale/binary variants, best first."""
    if cv2 is None:
        return [Variant("gray", _to_gray(img), "gray")]

    gray = _prepare_gray(img)
    normalized = _illumination_normalize(gray)
    enhanced = _sharpen(_clahe(normalized))

    variants = [
        Variant("sharpened", _border(enhanced), "gray"),
        Variant("normalized", _border(normalized), "gray"),
        Variant("grayscale", _border(gray), "gray"),
        Variant("adaptive", _border(_adaptive(enhanced)), "binary"),
        Variant("otsu", _border(_otsu(enhanced)), "binary"),
    ]

    if thorough:
        sauvola = _sauvola(enhanced)
        if sauvola is not None:
            variants.append(Variant("sauvola", _border(sauvola), "binary"))

    return variants
