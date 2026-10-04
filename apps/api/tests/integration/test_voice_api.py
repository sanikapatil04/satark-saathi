from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.core.database import get_db
from app.main import app
from app.services.stt import NoSpeechDetectedError, SttProcessingError, SttUnavailableError
from tests.helpers.audio import fake_mp3_header_bytes, minimal_wav_bytes

KYC_TEXT = (
    "Your bank KYC has expired. Your account will be blocked within 24 hours. "
    "Click this link immediately to update your account."
)
OTP_TEXT = "Urgent: Share your OTP and CVV immediately or your account will be blocked."
MONEY_TEXT = "Send money immediately by wire transfer to avoid legal action."
DIGITAL_ARREST_TEXT = (
    "This is cyber crime branch. You are under digital arrest. Transfer money now."
)
HARMLESS_TEXT = "Hello Amma, we will visit you on Sunday afternoon."
HINDI_TEXT = "अपना OTP तुरंत साझा करें, आपका खाता ब्लॉक हो जाएगा।"
MARATHI_TEXT = "तुमचा OTP लगेच शेअर करा, खाते ब्लॉक होईल."


async def override_get_db():
    mock_session = AsyncMock()
    mock_session.add = MagicMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock(side_effect=lambda record: setattr(record, "id", "voice-id"))
    yield mock_session


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def _post_voice(filename: str, content: bytes, content_type: str, language: str = "auto"):
    return client.post(
        "/api/v1/voice/analyze",
        files={"audio": (filename, content, content_type)},
        data={"language": language},
    )


def test_valid_audio_request_mocked_stt():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(KYC_TEXT, "en"),
    ):
        response = _post_voice("msg.wav", wav, "audio/wav")
    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == KYC_TEXT
    assert data["verdict"] in ("RED", "YELLOW", "GREEN")
    assert "spoken_response" in data
    assert len(data["spoken_response"]) > 10


def test_invalid_audio_type():
    response = _post_voice("notes.txt", b"hello", "text/plain")
    assert response.status_code == 400


def test_oversized_audio():
    wav = minimal_wav_bytes()
    with patch.object(settings, "VOICE_MAX_UPLOAD_BYTES", 50):
        response = _post_voice("big.wav", wav, "audio/wav")
    assert response.status_code == 400


def test_empty_audio():
    response = _post_voice("empty.wav", b"", "audio/wav")
    assert response.status_code == 400


def test_corrupted_audio():
    response = _post_voice("bad.wav", b"not-wav", "audio/wav")
    assert response.status_code == 400


def test_stt_success_boundary_mock():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=("Sample transcript for analysis.", "en"),
    ) as mock_stt:
        response = _post_voice("t.wav", wav, "audio/wav")
    assert response.status_code == 200
    mock_stt.assert_called_once()


def test_stt_failure():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        side_effect=SttProcessingError("fail"),
    ):
        response = _post_voice("t.wav", wav, "audio/wav")
    assert response.status_code == 422


def test_stt_unavailable():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        side_effect=SttUnavailableError("missing"),
    ):
        response = _post_voice("t.wav", wav, "audio/wav")
    assert response.status_code == 503


def test_analyzer_service_reuse():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(OTP_TEXT, "en"),
    ), patch(
        "app.api.v1.endpoints.voice.AnalyzerService.analyze_text",
        new_callable=AsyncMock,
        return_value={
            "id": "x",
            "verdict": "RED",
            "risk_score": 80,
            "category": "OTP_CREDENTIAL_THEFT",
            "reason": "test",
            "red_flags": ["OTP or credential request"],
            "recommended_action": "Never share OTP.",
        },
    ) as mock_analyze:
        response = _post_voice("otp.wav", wav, "audio/wav")
    assert response.status_code == 200
    mock_analyze.assert_awaited_once_with(OTP_TEXT, source="VOICE")


@pytest.mark.parametrize(
    "transcript,expected_category",
    [
        (KYC_TEXT, "BANK_KYC"),
        (OTP_TEXT, "OTP_CREDENTIAL_THEFT"),
        (MONEY_TEXT, "MONEY_TRANSFER"),
        (DIGITAL_ARREST_TEXT, "DIGITAL_ARREST"),
    ],
)
def test_scam_transcripts_mocked_stt(transcript, expected_category):
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(transcript, "en"),
    ):
        response = _post_voice("scam.wav", wav, "audio/wav")
    assert response.status_code == 200
    assert response.json()["category"] == expected_category


def test_harmless_transcript():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(HARMLESS_TEXT, "en"),
    ):
        response = _post_voice("safe.wav", wav, "audio/wav")
    assert response.status_code == 200
    assert response.json()["verdict"] == "GREEN"


def test_hindi_unicode_transcript():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(HINDI_TEXT, "hi"),
    ):
        response = _post_voice("hi.wav", wav, "audio/wav", language="hi")
    assert response.status_code == 200
    assert response.json()["transcript"] == HINDI_TEXT


def test_marathi_unicode_transcript():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(MARATHI_TEXT, "mr"),
    ):
        response = _post_voice("mr.wav", wav, "audio/wav", language="mr")
    assert response.status_code == 200
    assert response.json()["transcript"] == MARATHI_TEXT


def test_no_speech_detected():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        side_effect=NoSpeechDetectedError("no speech"),
    ):
        response = _post_voice("quiet.wav", wav, "audio/wav")
    assert response.status_code == 422


def test_database_persistence_voice_source():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(OTP_TEXT, "en"),
    ), patch(
        "app.repositories.analysis_repository.AnalysisRepository.create_analysis",
        new_callable=AsyncMock,
    ) as mock_create:
        mock_create.return_value = MagicMock(id="vid")
        response = _post_voice("p.wav", wav, "audio/wav")
    assert response.status_code == 200
    kwargs = mock_create.await_args.kwargs
    assert kwargs["source"] == "VOICE"
    assert kwargs["input_text"] == OTP_TEXT


def test_invalid_language_form():
    wav = minimal_wav_bytes()
    response = _post_voice("x.wav", wav, "audio/wav", language="fr")
    # STT raises AudioValidationError inside thread — mapped via processing or we validate upfront
    assert response.status_code in (400, 422)


def test_internal_error_handling():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(HARMLESS_TEXT, "en"),
    ), patch(
        "app.api.v1.endpoints.voice.AnalyzerService.analyze_text",
        side_effect=Exception("db exploded"),
    ):
        response = _post_voice("err.wav", wav, "audio/wav")
    assert response.status_code == 500
    assert "db exploded" not in response.json()["detail"].lower()


def test_spoken_response_in_api_response():
    wav = minimal_wav_bytes()
    with patch(
        "app.api.v1.endpoints.voice.SpeechToTextService.transcribe_or_raise",
        return_value=(OTP_TEXT, "en"),
    ):
        response = _post_voice("otp.wav", wav, "audio/wav")
    spoken = response.json()["spoken_response"]
    assert "OTP" in spoken or "Stop" in spoken
