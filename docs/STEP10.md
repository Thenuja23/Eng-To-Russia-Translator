# Step 10 - File ingestion: DOCX, PPTX, digital PDF, TXT

## Goal
Support TXT (detect Windows-1251 with charset-normalizer), DOCX, PPTX, digital PDF (per-page scan fallback if under ~20 chars). All become unified segments.

## Files
- backend/app/services/text_input/file_ingest.py
- backend/app/services/text_input/encodings.py

## Done when
- TXT reads with encoding detection
- DOCX parsing works
- PPTX parsing works
- PDF text extraction; fallback logic noted
- Unified to text pipeline
