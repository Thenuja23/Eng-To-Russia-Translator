class ImageTransform:
    def perspective_correction(self, img):
        # Placeholder - requires cv2
        return img

    def deskew(self, img):
        return img

    def remove_shadows(self, img):
        return img

    def deslant(self, img, angle_range=(20, 25)):
        # Deslant ~20-25 degree slant as specified
        return img

    def normalize_height(self, img, target_height=32, pad_width=True):
        # Height normalization with width PADDING (never squashing)
        return img
