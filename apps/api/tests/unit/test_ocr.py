import pytest

from app.core.config import settings
from app.services.ocr import (
    ImageValidationError,
    OCRService,
    OcrProcessingError,
    OcrUnavailableError,
)
from tests.helpers.images import minimal_png_bytes


def test_validate_rejects_empty_upload():
    with pytest.raises(ImageValidationError, match="No image"):
        OCRService.validate_upload(
            content_type="image/png",
            filename="shot.png",
            file_size=0,
            max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
            raw_bytes=b"",
        )


def test_validate_rejects_unsupported_mime():
    with pytest.raises(ImageValidationError, match="Unsupported file type"):
        OCRService.validate_upload(
            content_type="text/plain",
            filename="note.txt",
            file_size=4,
            max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
            raw_bytes=b"test",
        )


def test_validate_rejects_oversized_file():
    data = minimal_png_bytes()
    with pytest.raises(ImageValidationError, match="too large"):
        OCRService.validate_upload(
            content_type="image/png",
            filename="big.png",
            file_size=settings.SCREENSHOT_MAX_UPLOAD_BYTES + 1,
            max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
            raw_bytes=data,
        )


def test_validate_accepts_valid_png():
    data = minimal_png_bytes()
    mime = OCRService.validate_upload(
        content_type="image/png",
        filename="valid.png",
        file_size=len(data),
        max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
        raw_bytes=data,
    )
    assert mime == "image/png"


def test_validate_rejects_corrupted_image_bytes():
    with pytest.raises(ImageValidationError, match="not a readable image"):
        OCRService.validate_upload(
            content_type="image/png",
            filename="bad.png",
            file_size=32,
            max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
            raw_bytes=b"\x89PNG\r\n\x1a\n" + b"not-a-real-image" * 2,
        )


def test_extract_text_or_raise_empty(monkeypatch):
    service = OCRService()

    def fake_extract(_: bytes) -> str:
        return "  "

    monkeypatch.setattr(service, "extract_text", fake_extract)
    with pytest.raises(ValueError, match="Could not read enough text"):
        service.extract_text_or_raise(minimal_png_bytes())


def test_extract_text_tesseract_unavailable(monkeypatch):
    import pytesseract
    from pytesseract import TesseractNotFoundError

    monkeypatch.setattr(
        pytesseract,
        "get_tesseract_version",
        lambda: (_ for _ in ()).throw(TesseractNotFoundError()),
    )
    service = OCRService()
    with pytest.raises(OcrUnavailableError):
        service.extract_text(minimal_png_bytes())


def test_extract_text_processing_failure(monkeypatch):
    import pytesseract

    monkeypatch.setattr(pytesseract, "get_tesseract_version", lambda: "5.0")

    def boom(*_args, **_kwargs):
        raise RuntimeError("ocr broke")

    monkeypatch.setattr("app.services.ocr.Image.open", boom)
    service = OCRService()
    with pytest.raises(OcrProcessingError):
        service.extract_text(minimal_png_bytes())
