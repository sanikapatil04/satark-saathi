import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.repositories.analysis_repository import AnalysisRepository
from app.services.rules_engine import ScamRulesEngine

logger = logging.getLogger(__name__)


class AnalyzerService:
    """Service orchestrating text scam analysis, rule evaluation, and persistence."""

    def __init__(self, db_session: Optional[AsyncSession] = None):
        self.rules_engine = ScamRulesEngine()
        self.repository = AnalysisRepository(db_session) if db_session else None

    async def analyze_text(self, text: str, source: str = "TEXT") -> dict:
        """
        Orchestrate text analysis pipeline:
        1. Evaluate rules & scoring
        2. Persist record if DB session is present
        3. Return response data dictionary
        """
        (
            risk_score,
            verdict,
            category,
            red_flags,
            reason,
            recommended_action,
        ) = self.rules_engine.evaluate(text)

        # Sanitize logging: Log only verdict/score metadata, NEVER the raw message text
        logger.info(
            "Completed scam analysis: verdict=%s score=%d category=%s red_flags_count=%d",
            verdict,
            risk_score,
            category,
            len(red_flags),
        )

        analysis_id = None
        if self.repository:
            record = await self.repository.create_analysis(
                input_text=text,
                source=source,
                verdict=verdict,
                risk_score=risk_score,
                category=category,
                reason=reason,
                red_flags=red_flags,
                recommended_action=recommended_action,
            )
            analysis_id = record.id

        return {
            "id": analysis_id,
            "verdict": verdict,
            "risk_score": risk_score,
            "category": category,
            "reason": reason,
            "red_flags": red_flags,
            "recommended_action": recommended_action,
        }