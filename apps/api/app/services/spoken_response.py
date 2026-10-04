"""Senior-friendly spoken responses derived from analysis verdicts."""

from app.schemas.verdict import VerdictEnum

CAT_DIGITAL_ARREST = "DIGITAL_ARREST"
CAT_BANK_KYC = "BANK_KYC"
CAT_OTP_CREDENTIAL = "OTP_CREDENTIAL_THEFT"
CAT_MONEY_TRANSFER = "MONEY_TRANSFER"
CAT_AUTHORITY = "AUTHORITY_IMPERSONATION"
CAT_PRIZE_LOTTERY = "PRIZE_LOTTERY"
CAT_MALICIOUS_LINK = "MALICIOUS_LINK"


class SpokenResponseService:
    """Build short, clear text for browser or future local TTS playback."""

    @staticmethod
    def generate(verdict: str, category: str, recommended_action: str) -> str:
        if verdict == VerdictEnum.GREEN.value:
            return (
                "No major scam signs were detected. Still verify unexpected "
                "requests before sharing sensitive information."
            )

        if verdict == VerdictEnum.YELLOW.value:
            return (
                "Be careful. This message has warning signs. Verify it using "
                "an official source before taking action."
            )

        # RED — category-specific guidance first, then safe default.
        if category == CAT_DIGITAL_ARREST:
            return (
                "Stop. Do not send money or stay on the call. Digital arrest "
                "is not a legitimate legal process."
            )
        if category == CAT_OTP_CREDENTIAL:
            return "Stop. Never share your OTP, PIN, password, or CVV."
        if category == CAT_BANK_KYC:
            return (
                "Stop. Do not use the link in the message. Contact your bank "
                "using its official number."
            )
        if category == CAT_MONEY_TRANSFER:
            return (
                "Stop. This message looks dangerous. Do not send money or pay "
                "any fee."
            )
        if category == CAT_AUTHORITY:
            return (
                "Stop. This message looks dangerous. Do not panic or send money "
                "based on threats in a text or call."
            )
        if category == CAT_PRIZE_LOTTERY:
            return (
                "Stop. This message looks dangerous. Do not pay fees to claim "
                "a prize or lottery."
            )
        if category == CAT_MALICIOUS_LINK:
            return (
                "Stop. This message looks dangerous. Do not click suspicious "
                "links or share personal details."
            )

        if recommended_action:
            return f"Stop. This message looks dangerous. {recommended_action}"

        return (
            "Stop. This message looks dangerous. Do not share your OTP or send money."
        )
