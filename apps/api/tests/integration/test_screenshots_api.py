from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.services.ocr import NoTextExtractedError, OcrProcessingError, OcrUnavailableError
from tests.helpers.images import minimal_png_bytes

KYC_TEXT = (
    "Your bank KYC has expired. Your account will be blocked within 24 hours. "
    "Click this link immediately to update your account."
)
OTP_TEXT = (
    "Urgent: Share your OTP and CVV immediately or your account will be blocked."
)
PRIZE_TEXT = (
    "Congratulations lottery winner! You won a cashback reward. "
    "Act now limited time offer expires today."
)
DIGITAL_ARREST_TEXT = (
    "This is cyber crime branch. You are under digital arrest. Transfer money now."
)
HARMLESS_TEXT = "Hello Amma, we will visit you on Sunday afternoon."


async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda record: setattr(record, "id", "test-id"))
    yield mock_session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _post_screenshot(filename: str, content: bytes, content_type: str):
    return client.post(
        "/api/v1/screenshots/analyze",
        files={"image": (filename, content, content_type)},
    )


def test_valid_image_upload_with_mocked_ocr():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value=KYC_TEXT,
    ):
        response = _post_screenshot("kyc.png", png, "image/png")
    assert response.status_code == 200
    data = response.json()
    assert data["verdict"] == "RED"
    assert data["category"] == "BANK_KYC"
    assert data["extracted_text"] == KYC_TEXT


def test_unsupported_file_type():
    response = _post_screenshot("notes.txt", b"hello", "text/plain")
    assert response.status_code == 400
    assert "Unsupported" in response.json()["detail"]


def test_oversized_file():
    png = minimal_png_bytes()
    with patch.object(settings, "SCREENSHOT_MAX_UPLOAD_BYTES", 10):
        response = _post_screenshot("large.png", png, "image/png")
    assert response.status_code == 400
    assert "too large" in response.json()["detail"].lower()


def test_empty_upload():
    response = _post_screenshot("empty.png", b"", "image/png")
    assert response.status_code == 400


def test_corrupted_image():
    response = _post_screenshot(
        "bad.png",
        b"\x89PNG\r\n\x1a\n" + b"corrupt",
        "image/png",
    )
    assert response.status_code == 400


def test_ocr_extraction_mock():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value="Extracted sample text for analysis.",
    ) as mock_ocr:
        response = _post_screenshot("sample.png", png, "image/png")
    assert response.status_code == 200
    mock_ocr.assert_called_once()
    assert "Extracted sample" in response.json()["extracted_text"]


def test_ocr_failure():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        side_effect=OcrProcessingError("fail"),
    ):
        response = _post_screenshot("fail.png", png, "image/png")
    assert response.status_code == 422
    assert "Could not read text" in response.json()["detail"]


def test_ocr_unavailable():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        side_effect=OcrUnavailableError("missing"),
    ):
        response = _post_screenshot("fail.png", png, "image/png")
    assert response.status_code == 503


@pytest.mark.parametrize(
    "ocr_text,expected_category,expected_verdict",
    [
        (KYC_TEXT, "BANK_KYC", "RED"),
        (OTP_TEXT, "OTP_CREDENTIAL_THEFT", "RED"),
        (PRIZE_TEXT, "PRIZE_LOTTERY", "YELLOW"),
        (DIGITAL_ARREST_TEXT, "DIGITAL_ARREST", "RED"),
    ],
)
def test_scam_image_categories(ocr_text, expected_category, expected_verdict):
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value=ocr_text,
    ):
        response = _post_screenshot("scam.png", png, "image/png")
    assert response.status_code == 200
    data = response.json()
    assert data["category"] == expected_category
    assert data["verdict"] == expected_verdict


def test_harmless_image_text():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value=HARMLESS_TEXT,
    ):
        response = _post_screenshot("safe.png", png, "image/png")
    assert response.status_code == 200
    assert response.json()["verdict"] == "GREEN"


def test_no_readable_text():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        side_effect=NoTextExtractedError("no text"),
    ):
        response = _post_screenshot("blank.png", png, "image/png")
    assert response.status_code == 422


def test_analyzer_reuse():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value=KYC_TEXT,
    ), patch(
        "app.api.v1.endpoints.screenshots.AnalyzerService.analyze_text",
        new_callable=AsyncMock,
        return_value={
            "id": "abc",
            "verdict": "RED",
            "risk_score": 90,
            "category": "BANK_KYC",
            "reason": "test",
            "red_flags": ["Urgent action requested"],
            "recommended_action": "Do not click.",
        },
    ) as mock_analyze:
        response = _post_screenshot("reuse.png", png, "image/png")
    assert response.status_code == 200
    mock_analyze.assert_awaited_once_with(KYC_TEXT, source="SCREENSHOT")


def test_database_persistence_source_screenshot():
    png = minimal_png_bytes()
    with patch(
        "app.api.v1.endpoints.screenshots.OCRService.extract_text_or_raise",
        return_value=KYC_TEXT,
    ), patch(
        "app.repositories.analysis_repository.AnalysisRepository.create_analysis",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = MagicMock(id="persisted-id")
        response = _post_screenshot("persist.png", png, "image/png")
    assert response.status_code == 200
    mock_create.assert_awaited_once()
    kwargs = mock_create.await_args.kwargs
    assert kwargs["source"] == "SCREENSHOT"
    assert kwargs["input_text"] == KYC_TEXT
