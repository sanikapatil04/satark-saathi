from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.analysis import AnalysisRecord


class AnalysisRepository:
    """Repository handling database operations for AnalysisRecord."""

    def __init__(self, db_session: AsyncSession):
        self.session = db_session

    async def create_analysis(
        self,
        input_text: str,
        verdict: str,
        risk_score: int,
        category: str,
        reason: str,
        red_flags: list[str],
        recommended_action: str,
        source: str = "TEXT",
    ) -> AnalysisRecord:
        """Persist a new analysis record in the database."""
        record = AnalysisRecord(
            input_text=input_text,
            source=source,
            verdict=verdict,
            risk_score=risk_score,
            category=category,
            reason=reason,
            red_flags=red_flags,
            recommended_action=recommended_action,
        )
        self.session.add(record)
        await self.session.commit()
        await self.session.refresh(record)
        return record

    async def get_by_id(self, record_id: str) -> Optional[AnalysisRecord]:
        """Fetch an analysis record by primary key."""
        result = await self.session.execute(
            select(AnalysisRecord).where(AnalysisRecord.id == record_id)
        )
        return result.scalar_one_or_none()