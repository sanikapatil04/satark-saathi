import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.schemas.screenshot import ScreenshotAnalysisResponse
from app.services.analyzer import AnalyzerService
from app.services.ocr import (
    ImageValidationError,
    NoTextExtractedError,
    OCRService,
    OcrProcessingError,
    OcrUnavailableError,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/screenshots/analyze",
    response_model=ScreenshotAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze a screenshot for scam indicators",
    description=(
        "Accepts a screenshot image, extracts text via local OCR, and runs the "
        "same scam analysis pipeline as text submission."
    ),
)
async def analyze_screenshot(
    image: UploadFile = File(..., description="Screenshot image (JPEG, PNG, or WebP)"),
    db: AsyncSession = Depends(get_db),
) -> ScreenshotAnalysisResponse:
    """OCR a screenshot and analyze extracted text for scam indicators."""
    raw_bytes = await image.read()
    ocr_service = OCRService()

    try:
        OCRService.validate_upload(
            content_type=image.content_type,
            filename=image.filename,
            file_size=len(raw_bytes),
            max_bytes=settings.SCREENSHOT_MAX_UPLOAD_BYTES,
            raw_bytes=raw_bytes,
        )
    except ImageValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        extracted_text = ocr_service.extract_text_or_raise(raw_bytes)
    except NoTextExtractedError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except OcrUnavailableError:
        logger.error("OCR engine unavailable on this server")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Screenshot text reading is temporarily unavailable. "
                "Please type the message text instead."
            ),
        )
    except OcrProcessingError:
        logger.error("OCR processing failed for uploaded screenshot", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Could not read text from this screenshot. "
                "Try a clearer image or paste the message as text."
            ),
        )

    try:
        analyzer = AnalyzerService(db_session=db)
        result = await analyzer.analyze_text(extracted_text, source="SCREENSHOT")
        result["extracted_text"] = extracted_text
        return ScreenshotAnalysisResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error during screenshot analysis: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the screenshot.",
        ) from exc
