"""Local Tesseract OCR for screenshot text extraction.

English (`eng`) is used when available. Hindi (`hin`) and Marathi (`mar`) can be
enabled by installing the corresponding Tesseract language packs and extending
``OCRService.DEFAULT_LANG`` / ``build_tesseract_lang`` — multilingual OCR is not
claimed unless those packs are present on the host.
"""

from __future__ import annotations

import logging
from io import BytesIO
from typing import Optional

from PIL import Image, UnidentifiedImageError

logger = logging.getLogger(__name__)

# MIME types we accept (validated against actual image content via Pillow).
ALLOWED_IMAGE_MEDIA_TYPES: frozenset[str] = frozenset(
    {"image/jpeg", "image/png", "image/webp"}
)

ALLOWED_IMAGE_EXTENSIONS: frozenset[str] = frozenset({".jpg", ".jpeg", ".png", ".webp"})

# Minimum non-whitespace characters to treat OCR output as usable.
MIN_EXTRACTED_TEXT_LENGTH = 3


class ImageValidationError(ValueError):
    """Raised when an upload fails client-side validation."""


class OcrProcessingError(Exception):
    """Raised when OCR fails internally (not exposed to API clients)."""


class OcrUnavailableError(OcrProcessingError):
    """Raised when Tesseract is not installed or not on PATH."""


class NoTextExtractedError(ValueError):
    """Raised when OCR succeeds but yields no usable text."""


def build_tesseract_lang(preferred: Optional[str] = None) -> str:
    """Build Tesseract language string; extend when hi/mr packs are installed."""
    if preferred:
        return preferred
    # Default English only until hin/mar data files are verified on the host.
    return "eng"


class OCRService:
    """Extract text from screenshot bytes using local Tesseract OCR."""

    def __init__(self, tesseract_lang: Optional[str] = None):
        self.tesseract_lang = build_tesseract_lang(tesseract_lang)

    @staticmethod
    def validate_upload(
        *,
        content_type: Optional[str],
        filename: Optional[str],
        file_size: int,
        max_bytes: int,
        raw_bytes: bytes,
    ) -> str:
        """
        Validate MIME type, size, extension (hint only), and decodable image content.
        Returns normalized media type detected from image bytes.
        """
        if file_size == 0 or not raw_bytes:
            raise ImageValidationError("No image file was uploaded.")

        if file_size > max_bytes:
            raise ImageValidationError(
                f"Image is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB."
            )

        normalized_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_type not in ALLOWED_IMAGE_MEDIA_TYPES:
            raise ImageValidationError(
                "Unsupported file type. Upload a JPEG, PNG, or WebP screenshot."
            )

        if filename:
            lower_name = filename.lower()
            if not any(lower_name.endswith(ext) for ext in ALLOWED_IMAGE_EXTENSIONS):
                raise ImageValidationError(
                    "Unsupported file extension. Use .jpg, .jpeg, .png, or .webp."
                )

        try:
            image = Image.open(BytesIO(raw_bytes))
            image.verify()
            image = Image.open(BytesIO(raw_bytes))
            image.load()
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
            raise ImageValidationError(
                "The uploaded file is not a readable image."
            ) from exc

        fmt = (image.format or "").upper()
        format_to_mime = {"JPEG": "image/jpeg", "PNG": "image/png", "WEBP": "image/webp"}
        detected_mime = format_to_mime.get(fmt)
        if detected_mime is None or detected_mime not in ALLOWED_IMAGE_MEDIA_TYPES:
            raise ImageValidationError(
                "Unsupported image format. Upload a JPEG, PNG, or WebP screenshot."
            )

        if detected_mime != normalized_type and normalized_type in ALLOWED_IMAGE_MEDIA_TYPES:
            # Trust content over client-declared type when both are allowed formats.
            normalized_type = detected_mime

        image.close()
        return normalized_type

    def extract_text(self, raw_bytes: bytes) -> str:
        """Run OCR on image bytes and return stripped text."""
        try:
            import pytesseract
        except ImportError as exc:
            logger.error("pytesseract is not installed")
            raise OcrUnavailableError("OCR dependency missing") from exc

        try:
            pytesseract.get_tesseract_version()
        except pytesseract.TesseractNotFoundError as exc:
            logger.error("Tesseract binary not found on PATH")
            raise OcrUnavailableError("Tesseract not available") from exc

        try:
            image = Image.open(BytesIO(raw_bytes))
            text = pytesseract.image_to_string(image, lang=self.tesseract_lang)
        except Exception as exc:
            logger.error("OCR processing failed: %s", type(exc).__name__, exc_info=True)
            raise OcrProcessingError("OCR failed") from exc

        cleaned = " ".join(text.split())
        return cleaned

    def extract_text_or_raise(self, raw_bytes: bytes) -> str:
        """Extract text and raise if nothing usable was found."""
        text = self.extract_text(raw_bytes)
        if len(text.strip()) < MIN_EXTRACTED_TEXT_LENGTH:
            raise NoTextExtractedError(
                "Could not read enough text from the screenshot. "
                "Try a clearer image with visible message text."
            )
        return text

    @staticmethod
    def is_tesseract_available() -> bool:
        try:
            import pytesseract

            pytesseract.get_tesseract_version()
            return True
        except Exception:
            return False
