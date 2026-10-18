# Step 9 - Printed OCR (Tesseract) + editable OCR screen + tap-a-word view

## Goal
Add Tesseract-based printed OCR (baseline with rus.traineddata), editable OCR screen structure, and tap-a-word view. Include image preprocessing hooks.

## Files
- backend/app/services/ocr/base.py
- backend/app/services/ocr/tesseract_ocr.py
- backend/app/services/ocr/pipeline.py
- backend/app/services/ocr/__init__.py
- frontend/src/components/EditableOCRScreen.jsx
- frontend/src/components/TapWordView.jsx

## Done when
- OCR interface defined
- Tesseract OCR class with confidence, lines, words, bboxes
- Pipeline connects preprocessing + OCR
- Frontend components for editing and word tap view
