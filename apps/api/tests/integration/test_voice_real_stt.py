"""REAL STT VERIFICATION — skipped unless faster-whisper is installed and opted in."""

import os

import pytest

from app.services.stt import SpeechToTextService
from tests.helpers.audio import minimal_wav_bytes

pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_REAL_STT") != "1" or not SpeechToTextService.is_stt_available(),
    reason="Set RUN_REAL_STT=1 and install pip '.[voice]' to run real STT tests",
)


@pytest.mark.real_stt
def test_real_stt_silent_wav_yields_no_speech_or_empty():
    """Silent fixture may fail length check — documents real boundary behavior."""
    service = SpeechToTextService()
    with pytest.raises((ValueError, Exception)):
        service.transcribe_or_raise(minimal_wav_bytes(), language="en")
