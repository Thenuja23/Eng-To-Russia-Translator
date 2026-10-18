# Step 8 - OpenCV preprocessing: perspective, deskew, shadow removal, deslant, line segmentation

## Goal
Add preprocessing pipeline (OpenCV-based) for images: perspective correction, deskew, shadow removal, deslanting (~20-25°), height normalization with width padding (never squashing), line segmentation.

## Files
- backend/app/services/preprocessing/transform.py
- backend/app/services/preprocessing/lines.py
- backend/app/services/preprocessing/pipeline.py
- backend/app/services/preprocessing/__init__.py

## Notes
- OpenCV may not be installed; code should be import-safe with graceful errors.
- Deslant ~20-25° as specified.
