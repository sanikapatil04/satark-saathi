from app.services.spoken_response import SpokenResponseService


def test_spoken_response_green():
    text = SpokenResponseService.generate("GREEN", "GENERIC_SCAM", "")
    assert "No major scam signs" in text


def test_spoken_response_yellow():
    text = SpokenResponseService.generate("YELLOW", "GENERIC_SCAM", "")
    assert "Be careful" in text


def test_spoken_response_red_otp():
    text = SpokenResponseService.generate(
        "RED", "OTP_CREDENTIAL_THEFT", "Never share OTP."
    )
    assert "OTP" in text
    assert "Stop" in text


def test_spoken_response_digital_arrest():
    text = SpokenResponseService.generate("RED", "DIGITAL_ARREST", "")
    assert "Digital arrest" in text


def test_spoken_response_bank_kyc():
    text = SpokenResponseService.generate("RED", "BANK_KYC", "")
    assert "bank" in text.lower()
