"""Local speech-to-text for voice scam checks (CPU-friendly Whisper via faster-whisper).

Install optional dependency: ``pip install ".[voice]"`` (see pyproject.toml).
Model default: ``tiny`` (~75MB download on first use). No GPU required.
"""

from __future__ import annotations

import logging
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

ALLOWED_AUDIO_MEDIA_TYPES: frozenset[str] = frozenset(
    {
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "audio/webm",
        "video/webm",
        "audio/ogg",
        "application/ogg",
        "audio/mp4",
        "audio/x-m4a",
        "audio/m4a",
    }
)

ALLOWED_AUDIO_EXTENSIONS: frozenset[str] = frozenset(
    {".wav", ".mp3", ".webm", ".ogg", ".m4a", ".mp4"}
)

SUPPORTED_LANGUAGE_CODES: frozenset[str] = frozenset({"en", "hi", "mr", "auto"})

MIN_TRANSCRIPT_LENGTH = 3

# Whisper language codes (Marathi supported in multilingual tiny/base models).
WHISPER_LANG: dict[str, Optional[str]] = {
    "en": "en",
    "hi": "hi",
    "mr": "mr",
    "auto": None,
}


class AudioValidationError(ValueError):
    """Client-side audio upload validation failure."""


class SttProcessingError(Exception):
    """Internal STT failure (not exposed with stack traces)."""


class SttUnavailableError(SttProcessingError):
    """STT engine or optional dependency missing."""


class NoSpeechDetectedError(ValueError):
    """Transcription produced no usable speech."""


def _detect_container(raw_bytes: bytes) -> Optional[str]:
    if len(raw_bytes) < 12:
        return None
    if raw_bytes[:4] == b"RIFF" and raw_bytes[8:12] == b"WAVE":
        return "wav"
    if raw_bytes[:3] == b"ID3" or (
        len(raw_bytes) > 2 and raw_bytes[0] == 0xFF and (raw_bytes[1] & 0xE0) == 0xE0
    ):
        return "mp3"
    if raw_bytes[:4] == b"OggS":
        return "ogg"
    if raw_bytes[:4] == b"\x1aE\xdf\xa3":
        return "webm"
    if len(raw_bytes) > 8 and raw_bytes[4:8] == b"ftyp":
        return "m4a"
    return None


_CONTAINER_SUFFIX = {
    "wav": ".wav",
    "mp3": ".mp3",
    "ogg": ".ogg",
    "webm": ".webm",
    "m4a": ".m4a",
}


class SpeechToTextService:
    """Transcribe uploaded audio bytes using local faster-whisper (when installed)."""

    _shared_model = None
    _shared_model_key: Optional[tuple[str, str, str]] = None

    def __init__(
        self,
        model_size: Optional[str] = None,
        device: Optional[str] = None,
        compute_type: Optional[str] = None,
    ):
        from app.core.config import settings

        self.model_size = model_size or settings.STT_MODEL_SIZE
        self.device = device or settings.STT_DEVICE
        self.compute_type = compute_type or settings.STT_COMPUTE_TYPE

    @staticmethod
    def validate_upload(
        *,
        content_type: Optional[str],
        filename: Optional[str],
        file_size: int,
        max_bytes: int,
        raw_bytes: bytes,
    ) -> str:
        if file_size == 0 or not raw_bytes:
            raise AudioValidationError("No audio file was uploaded.")

        if file_size > max_bytes:
            raise AudioValidationError(
                f"Audio is too large. Maximum allowed size is {max_bytes // (1024 * 1024)} MB."
            )

        normalized_type = (content_type or "").split(";")[0].strip().lower()
        if normalized_type not in ALLOWED_AUDIO_MEDIA_TYPES:
            raise AudioValidationError(
                "Unsupported file type. Upload WAV, MP3, WebM, OGG, or M4A audio."
            )

        if filename:
            lower_name = filename.lower()
            if not any(lower_name.endswith(ext) for ext in ALLOWED_AUDIO_EXTENSIONS):
                raise AudioValidationError(
                    "Unsupported file extension. Use .wav, .mp3, .webm, .ogg, or .m4a."
                )

        container = _detect_container(raw_bytes)
        if container is None:
            raise AudioValidationError("The uploaded file is not readable audio.")

        return normalized_type

    @classmethod
    def is_stt_available(cls) -> bool:
        try:
            import faster_whisper  # noqa: F401

            return True
        except ImportError:
            return False

    def _get_model(self):
        try:
            from faster_whisper import WhisperModel
        except ImportError as exc:
            raise SttUnavailableError("faster-whisper is not installed") from exc

        key = (self.model_size, self.device, self.compute_type)
        if (
            SpeechToTextService._shared_model is not None
            and SpeechToTextService._shared_model_key == key
        ):
            return SpeechToTextService._shared_model

        logger.info(
            "Loading STT model size=%s device=%s compute=%s",
            self.model_size,
            self.device,
            self.compute_type,
        )
        model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
        )
        SpeechToTextService._shared_model = model
        SpeechToTextService._shared_model_key = key
        return model

    def transcribe(self, raw_bytes: bytes, language: str = "auto") -> tuple[str, Optional[str]]:
        """
        Transcribe audio bytes. Returns (transcript, detected_language_code).
        Does not log transcript content.
        """
        if language not in SUPPORTED_LANGUAGE_CODES:
            raise AudioValidationError(
                "Unsupported language. Use en, hi, mr, or auto."
            )

        whisper_lang = WHISPER_LANG[language]
        container = _detect_container(raw_bytes)
        if container is None:
            raise AudioValidationError("The uploaded file is not readable audio.")

        suffix = _CONTAINER_SUFFIX.get(container, ".wav")
        temp_path: Optional[Path] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(raw_bytes)
                temp_path = Path(tmp.name)

            model = self._get_model()
            segments, info = model.transcribe(
                str(temp_path),
                language=whisper_lang,
                vad_filter=True,
            )
            parts = [segment.text.strip() for segment in segments if segment.text.strip()]
            transcript = " ".join(parts).strip()
            detected = getattr(info, "language", None)
            return transcript, detected
        except SttUnavailableError:
            raise
        except AudioValidationError:
            raise
        except Exception as exc:
            logger.error("STT processing failed: %s", type(exc).__name__, exc_info=True)
            raise SttProcessingError("STT failed") from exc
        finally:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except OSError:
                    logger.warning("Could not delete temporary audio file")

    def transcribe_or_raise(self, raw_bytes: bytes, language: str = "auto") -> tuple[str, Optional[str]]:
        transcript, detected = self.transcribe(raw_bytes, language=language)
        if len(transcript.strip()) < MIN_TRANSCRIPT_LENGTH:
            raise NoSpeechDetectedError(
                "Could not detect enough speech in the audio. "
                "Try again with a clearer recording."
            )
        return transcript, detected
