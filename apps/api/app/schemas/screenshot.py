from pydantic import Field

from app.schemas.analysis import AnalysisResponse


class ScreenshotAnalysisResponse(AnalysisResponse):
    """Scam analysis result for screenshot uploads, including OCR text."""

    extracted_text: str = Field(
        ...,
        description="Text extracted from the screenshot via local OCR.",
    )
