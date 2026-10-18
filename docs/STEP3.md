# Step 3 - Text pipeline: normalize, per-line language detection, segmentation, direction auto-detect

## Goal
Build text pipeline that normalizes, detects language per line, segments into text segments, and auto-detects direction. All inputs become one internal list of text segments.

## Implementation plan
Create services/text_input with pipeline. Include normalization, language detection (fasttext/simple heuristic fallback), segmentation, direction detection.

## Files
- services/text_input/normalizer.py
- services/text_input/langdetect.py  
- services/text_input/segmenter.py
- services/text_input/direction.py
- services/text_input/pipeline.py
- services/text_input/__init__.py
- schemas/text.py
- api/routes/text.py (optional for this step, or just service)

## Done when
- Normalizer handles whitespace, punctuation, encodings
- Per-line language detection works for ru/en
- Segmentation produces consistent segments
- Direction auto-detect
