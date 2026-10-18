# Step 6 - FastAPI + Supabase schema + auth + history, text-only deploy

## Goal
Add Supabase schema (migrations), basic auth structure, history storage. Keep text-only for deploy.

## Files
- supabase/migrations/001_init.sql
- backend/app/core/supabase.py (if needed)
- backend/app/api/routes/auth.py (basic)
- backend/app/api/routes/history.py

## Done when
- Schema matches data model (profiles, uploaded_images, ocr_results, etc.)
- RLS concepts noted
- Basic routes in place
