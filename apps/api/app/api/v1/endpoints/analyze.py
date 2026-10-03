import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analyzer import AnalyzerService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze text for scam indicators",
    description=(
        "Evaluates submitted text content against deterministic scam detection rules. "
        "Returns a risk score, verdict (GREEN/YELLOW/RED), detected red flags, category, "
        "and senior-friendly recommendations."
    ),
)
async def analyze_text(
    payload: AnalysisRequest,
    db: AsyncSession = Depends(get_db),
) -> AnalysisResponse:
    """Analyze a suspicious message text for scam indicators."""
    try:
        service = AnalyzerService(db_session=db)
        result = await service.analyze_text(payload.text)
        return AnalysisResponse(**result)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Unexpected error during scam analysis: %s", str(exc), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing the analysis request.",
        )