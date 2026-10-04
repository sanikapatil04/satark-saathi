import asyncio
import logging

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.voice import VoiceAnalysisResponse
from app.services.analyzer import AnalyzerService
from app.services.spoken_response import SpokenResponseService
from app.services.stt import (
    AudioValidationError,
    NoSpeechDetectedError,
    SpeechToTextService,
    SttProcessingError,
    SttUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/voice/analyze",
    response_model=VoiceAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze spoken suspicious message (voice)",
    description=(
        "Upload a short audio recording of a suspicious message. "
        "**Accepted formats:** WAV, MP3, WebM, OGG, M4A (max size from server config, default 10 MB). "
        "**Language:** optional form field `language` — `en`, `hi`, `mr`, or `auto` (default). "
        "Speech is converted to text using **local faster-whisper** (CPU, tiny model) when installed; "
        "audio is not sent to external AI services and is not stored permanently. "
        "The transcript is analyzed with the same rules engine as text and screenshot checks. "
        "**Limitations:** Hindi/Marathi accuracy depends on the local model and environment; "
        "without the optional `voice` dependencies, STT returns 503."
    ),
)
async def analyze_voice(
    audio: UploadFile = File(..., description="Audio recording (WAV, MP3, WebM, OGG, M4A)"),
    language: str = Form(
        "auto",
        description="Speech language hint: en, hi, mr, or auto-detect.",
    ),
    db: AsyncSession = Depends(get_db),
) -> VoiceAnalysisResponse:
    """Transcribe audio and analyze the transcript for scam indicators."""
    raw_bytes = await audio.read()
    stt_service = SpeechToTextService()

    try:
        SpeechToTextService.validate_upload(
            content_type=audio.content_type,
            filename=audio.filename,
            file_size=len(raw_bytes),
            max_bytes=settings.VOICE_MAX_UPLOAD_BYTES,
            raw_bytes=raw_bytes,
        )
    except AudioValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        transcript, detected_language = await asyncio.to_thread(
            stt_service.transcribe_or_raise,
            raw_bytes,
            language.strip().lower() if language else "auto",
        )
    except NoSpeechDetectedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except SttUnavailableError:
        logger.error("Local STT engine unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Voice recognition is temporarily unavailable on this server. "
                "Please type the message as text instead."
            ),
        )
    except SttProcessingError:
        logger.error("STT failed for uploaded audio", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Could not understand the audio. Try a clearer recording or paste the message as text."
            ),
        )

    try:
        analyzer = AnalyzerService(db_session=db)
        result = await analyzer.analyze_text(transcript, source="VOICE")
        spoken = SpokenResponseService.generate(
            verdict=result["verdict"],
            category=result["category"],
            recommended_action=result["recommended_action"],
        )
        result["transcript"] = transcript
        result["spoken_response"] = spoken
        result["detected_language"] = detected_language
        return VoiceAnalysisResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error during voice analysis: %s", type(exc).__name__, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the voice request.",
        ) from exc
