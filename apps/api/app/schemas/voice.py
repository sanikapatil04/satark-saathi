from typing import Optional

from pydantic import Field

from app.schemas.analysis import AnalysisResponse


class VoiceAnalysisResponse(AnalysisResponse):
    """Scam analysis from voice input, including transcript and spoken guidance."""

    transcript: str = Field(
        ...,
        description="Speech-to-text transcript of the uploaded audio (local STT).",
    )
    spoken_response: str = Field(
        ...,
        description=(
            "Short, senior-friendly text to read aloud (browser SpeechSynthesis or future TTS)."
        ),
    )
    detected_language: Optional[str] = Field(
        default=None,
        description="Language code detected by STT when language=auto, if available.",
    )
