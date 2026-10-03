from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.verdict import ScamCategoryEnum, VerdictEnum


class AnalysisRequest(BaseModel):
    """Input payload for text scam analysis."""

    text: str = Field(
        ...,
        description="The suspicious message or text content to analyze.",
        min_length=1,
        max_length=5000,
        examples=["Your bank KYC has expired. Click this link immediately to update your account."],
    )

    @field_validator("text")
    @classmethod
    def validate_non_whitespace(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Text content cannot be empty or contain only whitespace.")
        return v.strip()


class AnalysisResponse(BaseModel):
    """Output payload returned by the scam analysis engine."""

    id: Optional[str] = Field(
        default=None,
        description="Unique identifier of the saved analysis record.",
    )
    verdict: VerdictEnum = Field(
        ...,
        description="Overall scam verdict (GREEN, YELLOW, or RED).",
    )
    risk_score: int = Field(
        ...,
        ge=0,
        le=100,
        description="Deterministic risk score between 0 and 100.",
    )
    category: ScamCategoryEnum = Field(
        ...,
        description="Primary detected scam category.",
    )
    reason: str = Field(
        ...,
        description="Clear, non-technical explanation suitable for senior citizens.",
    )
    red_flags: List[str] = Field(
        ...,
        description="List of detected scam indicators and red flags.",
    )
    recommended_action: str = Field(
        ...,
        description="Safe, simple recommended action for the user.",
    )