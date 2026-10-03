# OCR language support

Screenshot analysis uses **local Tesseract OCR** (`apps/api/app/services/ocr.py`).

## Current phase

- **English (`eng`)** is the default and required language for Phase 2.
- Hindi and Marathi are **not enabled by default** until the matching Tesseract language data files are installed on the server.

## Enabling Hindi or Marathi later

1. Install language packs on the host (e.g. `tesseract-ocr-hin`, `tesseract-ocr-mar` on Debian/Ubuntu).
2. Update `build_tesseract_lang()` in `ocr.py` to include `hin` and/or `mar` (e.g. `eng+hin`).
3. Verify extraction with real screenshot fixtures before documenting user-facing support.

Do not enable language codes in production until the packs are verified on that environment.
