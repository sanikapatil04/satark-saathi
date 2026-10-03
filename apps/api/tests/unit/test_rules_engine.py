import pytest
from app.services.rules_engine import (
    ScamRulesEngine,
    VERDICT_GREEN,
    VERDICT_YELLOW,
    VERDICT_RED,
    CAT_BANK_KYC,
    CAT_OTP_CREDENTIAL,
    CAT_MONEY_TRANSFER,
    CAT_AUTHORITY,
    CAT_DIGITAL_ARREST,
    CAT_PRIZE_LOTTERY,
    CAT_MALICIOUS_LINK,
    CAT_GENERIC_SCAM,
)


@pytest.fixture
def engine():
    return ScamRulesEngine()


def test_harmless_message_green(engine):
    text = "Hi, are we still meeting tomorrow at 5 PM?"
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score <= 29
    assert verdict == VERDICT_GREEN
    assert category == CAT_GENERIC_SCAM
    assert len(red_flags) == 0


def test_bank_kyc_urgency_high_risk(engine):
    # KYC Expired (+15) + Urgency (+15) + Suspicious Link (+20) = 50 (YELLOW)
    text_yellow = "Your bank KYC has expired. Click this link immediately to update your account."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text_yellow)
    assert score == 50
    assert verdict == VERDICT_YELLOW
    assert category == CAT_BANK_KYC
    assert "Bank or KYC update request" in red_flags

    # KYC Expired (+15) + Urgency (+15) + Suspicious Link (+20) + Threat/Account Blocked (+20) = 70 (RED)
    text_red = "Your bank KYC has expired. Your account will be blocked within 24 hours. Click this link immediately to update your account."
    score_red, verdict_red, category_red, red_flags_red, _, _ = engine.evaluate(text_red)
    assert score_red >= 60
    assert verdict_red == VERDICT_RED
    assert category_red == CAT_BANK_KYC


def test_otp_request_red(engine):
    # OTP (+30) + Authority/Bank Officer (+20) + Urgency (+15) = 65 (RED)
    text = "URGENT: Your OTP is 123456. Please share it with the bank officer immediately to avoid account block."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 60
    assert verdict == VERDICT_RED
    assert category in (CAT_OTP_CREDENTIAL, CAT_BANK_KYC, CAT_AUTHORITY)
    assert "OTP or credential request" in red_flags


def test_money_transfer_red(engine):
    # Money Request (+30) + Urgency (+15) + Threat (+20) = 65 (RED)
    text = "Pay processing fee of ₹500 immediately to transfer money or legal action will be taken."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 60
    assert verdict == VERDICT_RED
    assert category in (CAT_MONEY_TRANSFER, CAT_GENERIC_SCAM)
    assert "Money transfer or fee request" in red_flags


def test_prize_message_yellow_or_red(engine):
    # Prize (+15) + Urgency (+15) + Link (+20) = 50 (YELLOW)
    text = "Congratulations! You won a prize in lucky draw. Click this link immediately to claim reward."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 30
    assert verdict in (VERDICT_YELLOW, VERDICT_RED)
    assert category in (CAT_PRIZE_LOTTERY, CAT_MALICIOUS_LINK)
    assert "Prize, lottery or cashback offer" in red_flags


def test_authority_impersonation(engine):
    # Authority (+20) + Threat/Warrant (+20) = 40 (YELLOW)
    text = "This is CBI officer. Warrant issued and case registered against you."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 30
    assert category in (CAT_AUTHORITY, CAT_GENERIC_SCAM)
    assert "Authority or government impersonation" in red_flags


def test_digital_arrest_red(engine):
    # Digital arrest (+40) + Authority/Police (+20) + Money Transfer (+30) = 90 (RED)
    text = "You are under digital arrest. Stay on this video call with police and transfer money to avoid arrest."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 60
    assert verdict == VERDICT_RED
    assert category == CAT_DIGITAL_ARREST
    assert "Digital arrest scam indicators" in red_flags
    assert "Digital arrest is not a legitimate legal process" in action


def test_suspicious_link_elevated_risk(engine):
    text = "Verify here to avoid account blocked http://suspicious-domain.xyz/login"
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert score >= 30
    assert "Suspicious link request" in red_flags


def test_mixed_language_hindi_marathi(engine):
    text = "Aapka account block ho jayega. Click link immediately."
    score, verdict, category, red_flags, reason, action = engine.evaluate(text)
    assert isinstance(score, int)
    assert verdict in (VERDICT_GREEN, VERDICT_YELLOW, VERDICT_RED)


def test_duplicate_keywords_single_contribution(engine):
    text = "OTP PIN password CVV verification code send OTP"
    score1, _, _, red_flags1, _, _ = engine.evaluate(text)
    single_text = "OTP"
    score2, _, _, red_flags2, _, _ = engine.evaluate(single_text)
    # Both trigger RULE_OTP_CREDENTIAL once (+30 points)
    assert score1 == 30
    assert score2 == 30


def test_score_max_cap(engine):
    text = (
        "Urgent! Immediately pay ₹5000 processing fee. OTP PIN CVV. "
        "Under digital arrest, CBI officer, bank KYC expired. Click http://scam.xyz"
    )
    score, verdict, _, _, _, _ = engine.evaluate(text)
    assert score == 100
    assert verdict == VERDICT_RED


def test_score_min_floor(engine):
    text = "Hello world welcome"
    score, verdict, _, _, _, _ = engine.evaluate(text)
    assert score == 0
    assert verdict == VERDICT_GREEN


def test_verdict_thresholds(engine):
    # 0 - 29 -> GREEN
    # 30 - 59 -> YELLOW
    # 60 - 100 -> RED
    assert engine.evaluate("hello friend")[0] <= 29
    assert engine.evaluate("hello friend")[1] == VERDICT_GREEN

    assert engine.evaluate("Urgent action required")[0] == 15
    assert engine.evaluate("Urgent action required")[1] == VERDICT_GREEN

    assert engine.evaluate("Urgent action required, keep this confidential")[0] == 35
    assert engine.evaluate("Urgent action required, keep this confidential")[1] == VERDICT_YELLOW

    assert engine.evaluate("Your OTP is 123456. Pay now immediately")[0] == 75
    assert engine.evaluate("Your OTP is 123456. Pay now immediately")[1] == VERDICT_RED


def test_category_tie_breaking(engine):
    # If both DIGITAL_ARREST (+40) and OTP (+30) match, DIGITAL_ARREST has higher category priority
    text = "Digital arrest stay on video call and send your OTP"
    _, _, category, _, _, _ = engine.evaluate(text)
    assert category == CAT_DIGITAL_ARREST


def test_input_normalization(engine):
    normalized = engine.normalize_text("  URGENT!!!  Click   Here...  ")
    assert "urgent click here" in normalized
