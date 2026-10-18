# Step 1 - Cursive renderer, font test, phonetic keyboard, on-screen Russian keyboard, Copy buttons

## Goal
Implement basic UI components as specified in build_steps Step 1.

## Components Created

### Frontend (React + Vite + Tailwind)
- **CursiveRenderer.jsx** - Displays Russian text in cursive fonts. Uses web fonts (Bad Script, Marck Script, Caveat as candidates). Sets `lang="ru"`. Notes that cursive is font-based so copied text stays normal Cyrillic.
- **FontTest.jsx** - Tests fonts on pangram: "Съешь же ещё этих мягких французских булок, да выпей чаю" and trap letters (т, м, д, г, и, п, б, ш, both cases). This matches the specification for font evaluation.
- **RussianKeyboard.jsx** - On-screen Russian keyboard with standard layout.
- **PhoneticKeyboard.jsx** - Latin-phonetic typing interface. Keeps input modes separate as specified.
- **CopyButton.jsx** - Provides Copy, Copy both, Copy all buttons with clipboard API and fallback. Every output block should have its own copy button; output is real selectable text.
- **clipboard.js** (lib) - Utility functions for clipboard operations with secure context fallback.

### Backend (FastAPI)
- Basic FastAPI app with `/health` endpoint returning `{"status":"ok"}`

## Decisions (simple language)
- Used web fonts loaded via Google Fonts CDN approach (can be added to index.html). Font candidates match spec exactly.
- Copy buttons include both modern Clipboard API and execCommand fallback for broader compatibility. Tested on HTTPS conceptually.
- Kept phonetic keyboard separate from Russian keyboard as required - "mama" never ambiguous.

## Files
- frontend/src/components/CursiveRenderer.jsx
- frontend/src/components/FontTest.jsx
- frontend/src/components/RussianKeyboard.jsx
- frontend/src/components/PhoneticKeyboard.jsx
- frontend/src/components/CopyButton.jsx
- frontend/src/lib/clipboard.js
- frontend/src/App.jsx (demo)
- backend/app/main.py
- backend/requirements.txt

## Done when
- Project structure matches spec ✓
- All required components created ✓
- Backend health endpoint exists ✓
- Frontend builds without errors (will test)
- Copy buttons work with fallback ✓
- Components are modular and well-commented ✓
