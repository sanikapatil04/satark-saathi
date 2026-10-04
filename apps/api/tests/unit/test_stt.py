import pytest

from app.core.config import settings
from app.services.stt import (
    AudioValidationError,
    SpeechToTextService,
    SttProcessingError,
)
from tests.helpers.audio import fake_mp3_header_bytes, minimal_wav_bytes


def test_validate_rejects_empty_audio():
    with pytest.raises(AudioValidationError, match="No audio"):
        SpeechToTextService.validate_upload(
            content_type="audio/wav",
            filename="x.wav",
            file_size=0,
            max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
            raw_bytes=b"",
        )


def test_validate_rejects_unsupported_mime():
    with pytest.raises(AudioValidationError, match="Unsupported file type"):
        SpeechToTextService.validate_upload(
            content_type="text/plain",
            filename="x.txt",
            file_size=4,
            max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
            raw_bytes=b"test",
        )


def test_validate_rejects_oversized():
    data = minimal_wav_bytes()
    with pytest.raises(AudioValidationError, match="too large"):
        SpeechToTextService.validate_upload(
            content_type="audio/wav",
            filename="big.wav",
            file_size=settings.VOICE_MAX_UPLOAD_BYTES + 1,
            max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
            raw_bytes=data,
        )


def test_validate_accepts_wav():
    data = minimal_wav_bytes()
    mime = SpeechToTextService.validate_upload(
        content_type="audio/wav",
        filename="ok.wav",
        file_size=len(data),
        max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
        raw_bytes=data,
    )
    assert mime == "audio/wav"


def test_validate_rejects_corrupted_container():
    with pytest.raises(AudioValidationError, match="not readable audio"):
        SpeechToTextService.validate_upload(
            content_type="audio/wav",
            filename="bad.wav",
            file_size=20,
            max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
            raw_bytes=b"not-a-wav-file-at-all",
        )


def test_validate_accepts_mp3_magic():
    data = fake_mp3_header_bytes()
    SpeechToTextService.validate_upload(
        content_type="audio/mpeg",
        filename="x.mp3",
        file_size=len(data),
        max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
        raw_bytes=data,
    )


def test_transcribe_or_raise_no_speech(monkeypatch):
    service = SpeechToTextService()

    def fake_transcribe(_raw: bytes, language: str = "auto"):
        return "  ", None

    monkeypatch.setattr(service, "transcribe", fake_transcribe)
    with pytest.raises(ValueError, match="Could not detect enough speech"):
        service.transcribe_or_raise(minimal_wav_bytes())


def test_transcribe_processing_failure(monkeypatch):
    service = SpeechToTextService()

    def boom(_raw: bytes, language: str = "auto"):
        raise RuntimeError("decode failed")

    monkeypatch.setattr(service, "transcribe", boom)
    with pytest.raises(SttProcessingError):
        service.transcribe(minimal_wav_bytes())
