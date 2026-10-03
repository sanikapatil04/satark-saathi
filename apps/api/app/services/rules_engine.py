import re
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple

# Constants & Thresholds
SCORE_GREEN_MAX = 29
SCORE_YELLOW_MAX = 59
MAX_RISK_SCORE = 100
MIN_RISK_SCORE = 0

VERDICT_GREEN = "GREEN"
VERDICT_YELLOW = "YELLOW"
VERDICT_RED = "RED"

# Scam Categories
CAT_BANK_KYC = "BANK_KYC"
CAT_OTP_CREDENTIAL = "OTP_CREDENTIAL_THEFT"
CAT_MONEY_TRANSFER = "MONEY_TRANSFER"
CAT_AUTHORITY = "AUTHORITY_IMPERSONATION"
CAT_DIGITAL_ARREST = "DIGITAL_ARREST"
CAT_PRIZE_LOTTERY = "PRIZE_LOTTERY"
CAT_MALICIOUS_LINK = "MALICIOUS_LINK"
CAT_GENERIC_SCAM = "GENERIC_SCAM"

# Category Priority for Deterministic Selection (Higher index = higher priority)
CATEGORY_PRIORITY: Dict[str, int] = {
    CAT_GENERIC_SCAM: 0,
    CAT_PRIZE_LOTTERY: 1,
    CAT_MALICIOUS_LINK: 2,
    CAT_MONEY_TRANSFER: 3,
    CAT_AUTHORITY: 4,
    CAT_BANK_KYC: 5,
    CAT_OTP_CREDENTIAL: 6,
    CAT_DIGITAL_ARREST: 7,
}


@dataclass
class RuleDefinition:
    rule_id: str
    category: str
    score_weight: int
    red_flag: str
    keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)


# Defined Rules as per prompt requirements
RULES: List[RuleDefinition] = [
    RuleDefinition(
        rule_id="RULE_URGENCY",
        category=CAT_GENERIC_SCAM,
        score_weight=15,
        red_flag="Urgent action requested",
        keywords=[
            "immediately",
            "urgent",
            "act now",
            "within 24 hours",
            "account will be blocked",
            "last warning",
            "urgently",
            "immediate action",
            "expires today",
        ],
        patterns=[r"block(?:ed)?\s+within", r"last\s+chance"],
    ),
    RuleDefinition(
        rule_id="RULE_SECRECY",
        category=CAT_GENERIC_SCAM,
        score_weight=20,
        red_flag="Secrecy or isolation requested",
        keywords=[
            "don't tell anyone",
            "dont tell anyone",
            "keep this confidential",
            "do not inform your family",
            "dont inform family",
            "stay on the call",
            "keep secret",
            "do not disconnect",
        ],
        patterns=[r"don'?t\s+tell\s+(anyone|family|bank)"],
    ),
    RuleDefinition(
        rule_id="RULE_OTP_CREDENTIAL",
        category=CAT_OTP_CREDENTIAL,
        score_weight=30,
        red_flag="OTP or credential request",
        keywords=[
            "otp",
            "pin",
            "password",
            "cvv",
            "upi pin",
            "verification code",
            "security pin",
            "one time password",
            "send otp",
            "share otp",
        ],
        patterns=[r"\b(otp|pin|cvv)\b", r"verification\s+code"],
    ),
    RuleDefinition(
        rule_id="RULE_MONEY_REQUEST",
        category=CAT_MONEY_TRANSFER,
        score_weight=30,
        red_flag="Money transfer or fee request",
        keywords=[
            "send money",
            "transfer",
            "payment required",
            "pay now",
            "processing fee",
            "security deposit",
            "transfer money",
            "deposit money",
            "advance fee",
            "pay fee",
        ],
        patterns=[r"pay\s+₹?\d+", r"transfer\s+₹?\d+", r"fee\s+of\s+₹?\d+"],
    ),
    RuleDefinition(
        rule_id="RULE_AUTHORITY_IMPERSONATION",
        category=CAT_AUTHORITY,
        score_weight=20,
        red_flag="Authority or government impersonation",
        keywords=[
            "police",
            "cbi",
            "rbi",
            "bank officer",
            "government officer",
            "income tax",
            "court",
            "cyber crime officer",
            "customs department",
            "enforcement directorate",
            "ed officer",
        ],
        patterns=[r"cyber\s*crime", r"bank\s*officer"],
    ),
    RuleDefinition(
        rule_id="RULE_THREAT_FEAR",
        category=CAT_GENERIC_SCAM,
        score_weight=20,
        red_flag="Threats or legal pressure",
        keywords=[
            "arrested",
            "account blocked",
            "legal action",
            "case registered",
            "warrant",
            "penalty",
            "arrest warrant",
            "court notice",
            "jail",
        ],
        patterns=[r"under\s+arrest", r"legal\s+action", r"account\s+(will\s+be\s+)?blocked"],
    ),
    RuleDefinition(
        rule_id="RULE_REWARD_PRIZE",
        category=CAT_PRIZE_LOTTERY,
        score_weight=15,
        red_flag="Prize, lottery or cashback offer",
        keywords=[
            "lottery",
            "prize",
            "winner",
            "cashback",
            "reward",
            "lucky draw",
            "you won",
            "claim prize",
            "claim reward",
        ],
        patterns=[r"won\s+₹?\d+", r"congratulations.*winner"],
    ),
    RuleDefinition(
        rule_id="RULE_KYC_BANK",
        category=CAT_BANK_KYC,
        score_weight=15,
        red_flag="Bank or KYC update request",
        keywords=[
            "kyc expired",
            "kyc update",
            "bank account",
            "account verification",
            "update kyc",
            "kyc suspended",
            "bank kyc",
            "pan card update",
            "aadhaar update",
        ],
        patterns=[r"kyc\s*(expired|update|suspended)", r"update\s+account"],
    ),
    RuleDefinition(
        rule_id="RULE_SUSPICIOUS_LINK",
        category=CAT_MALICIOUS_LINK,
        score_weight=20,
        red_flag="Suspicious link request",
        keywords=[
            "click this link",
            "open the link",
            "verify here",
            "update here",
            "click here",
            "login here",
        ],
        patterns=[
            r"https?://[^\s]+",
            r"bit\.ly/[^\s]+",
            r"tinyurl\.com/[^\s]+",
            r"t\.co/[^\s]+",
            r"[a-zA-Z0-9-]+\.(xyz|top|click|link|site|club|work|info|online)\b",
        ],
    ),
    RuleDefinition(
        rule_id="RULE_DIGITAL_ARREST",
        category=CAT_DIGITAL_ARREST,
        score_weight=40,
        red_flag="Digital arrest scam indicators",
        keywords=[
            "digital arrest",
            "stay on video call",
            "police verification through video",
            "aadhaar linked crime",
            "money required to avoid arrest",
            "video verification arrest",
            "under digital arrest",
        ],
        patterns=[r"digital\s+arrest", r"video\s+call.*arrest", r"stay\s+on\s+(this\s+)?video\s+call"],
    ),
]


class ScamRulesEngine:
    """Deterministic rules engine for evaluating text for scam indicators."""

    @staticmethod
    def normalize_text(text: str) -> str:
        """Safely normalize text for rule evaluation (case, spaces, punctuation)."""
        if not text:
            return ""
        # Lowercase
        normalized = text.lower()
        # Replace non-alphanumeric (except standard space and basic URL chars) with space
        normalized = re.sub(r"[^\w\s://.-]", " ", normalized)
        # Collapse multiple spaces
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized

    def evaluate(self, raw_text: str) -> Tuple[int, str, str, List[str], str, str]:
        """
        Evaluates the input text against scam detection rules.

        Returns:
            Tuple of:
            - risk_score (int 0-100)
            - verdict ("GREEN", "YELLOW", "RED")
            - primary_category (str)
            - red_flags (List[str])
            - reason (str)
            - recommended_action (str)
        """
        normalized_text = self.normalize_text(raw_text)

        raw_lower = raw_text.lower()

        matched_rules: List[RuleDefinition] = []
        detected_categories: Set[str] = set()
        detected_red_flags: List[str] = []

        # Evaluate rules - each rule triggers at most once
        for rule in RULES:
            triggered = False
            # Check keywords in both raw lower and normalized text
            for kw in rule.keywords:
                kw_lower = kw.lower()
                if kw_lower in raw_lower or kw_lower in normalized_text:
                    triggered = True
                    break

            if not triggered:
                # Check regex patterns
                for pat in rule.patterns:
                    if re.search(pat, raw_lower) or re.search(pat, normalized_text):
                        triggered = True
                        break

            if triggered:
                matched_rules.append(rule)
                detected_categories.add(rule.category)
                if rule.red_flag not in detected_red_flags:
                    detected_red_flags.append(rule.red_flag)

        # Calculate score (deduplicated per rule definition)
        raw_score = sum(rule.score_weight for rule in matched_rules)
        risk_score = min(MAX_RISK_SCORE, max(MIN_RISK_SCORE, raw_score))

        # Determine Verdict
        if risk_score <= SCORE_GREEN_MAX:
            verdict = VERDICT_GREEN
        elif risk_score <= SCORE_YELLOW_MAX:
            verdict = VERDICT_YELLOW
        else:
            verdict = VERDICT_RED

        # Determine Primary Category
        primary_category = self._select_primary_category(matched_rules)

        # Generate Reason
        reason = self._generate_reason(matched_rules, primary_category, verdict)

        # Generate Recommended Action
        recommended_action = self._generate_recommended_action(primary_category, verdict)

        return risk_score, verdict, primary_category, detected_red_flags, reason, recommended_action

    def _select_primary_category(self, matched_rules: List[RuleDefinition]) -> str:
        """Select primary category deterministically based on rule priorities and scores."""
        if not matched_rules:
            return CAT_GENERIC_SCAM

        # Sort categories present in matched rules by priority score descending
        categories_with_priority = [
            (rule.category, CATEGORY_PRIORITY.get(rule.category, 0), rule.score_weight)
            for rule in matched_rules
        ]
        # Sort by priority desc, then weight desc, then category name asc for deterministic tie-break
        categories_with_priority.sort(key=lambda x: (x[1], x[2], x[0]), reverse=True)

        return categories_with_priority[0][0]

    def _generate_reason(self, matched_rules: List[RuleDefinition], category: str, verdict: str) -> str:
        """Generates a clear, non-technical reason tailored for senior citizens."""
        if verdict == VERDICT_GREEN:
            return "No obvious scam patterns or suspicious financial requests were detected in this message."

        triggered_flags = [r.red_flag.lower() for r in matched_rules]

        if category == CAT_DIGITAL_ARREST:
            return "The message impersonates law enforcement and threatens arrest to force money transfers."
        elif category == CAT_BANK_KYC:
            return "The message creates urgency and asks you to update bank information or click a link."
        elif category == CAT_OTP_CREDENTIAL:
            return "The message asks for sensitive security credentials like an OTP, PIN, or verification code."
        elif category == CAT_AUTHORITY:
            return "The message impersonates an authority figure or government official to create fear."
        elif category == CAT_MONEY_TRANSFER:
            return "The message pressures you to send money, pay a fee, or make an urgent wire transfer."
        elif category == CAT_PRIZE_LOTTERY:
            return "The message promises a lottery, prize, or cashback reward to trick you into taking action."
        elif category == CAT_MALICIOUS_LINK:
            return "The message asks you to click a suspicious link that may steal your personal information."

        if triggered_flags:
            flags_str = ", ".join(triggered_flags[:2])
            return f"The message shows suspicious indicators including {flags_str}."

        return "The message contains suspicious patterns commonly associated with digital fraud."

    def _generate_recommended_action(self, category: str, verdict: str) -> str:
        """Generates safe, simple, senior-friendly advice."""
        if verdict == VERDICT_GREEN:
            return "No major scam indicators were detected. Still verify unexpected requests before sharing sensitive information."

        if verdict == VERDICT_YELLOW:
            return "Do not act yet. Verify the sender independently using an official phone number or website."

        # VERDICT_RED category-specific recommendations
        if category == CAT_DIGITAL_ARREST:
            return "Stop the interaction. Do not send money or stay on the call. Digital arrest is not a legitimate legal process."
        elif category == CAT_BANK_KYC:
            return "Do not use the link in the message. Contact your bank using its official website or number."
        elif category == CAT_OTP_CREDENTIAL:
            return "Never share an OTP, PIN, password, or CVV with anyone."
        elif category == CAT_MONEY_TRANSFER:
            return "Do not send any money or pay processing fees. Verify directly with the intended recipient."
        elif category == CAT_AUTHORITY:
            return "Do not panic or follow instructions. Real government officials do not demand immediate online payments over text."
        elif category == CAT_PRIZE_LOTTERY:
            return "Do not pay any advance fee or share personal details. Legitimate lotteries do not ask for money to claim prizes."

        return "Do not click links, share OTPs, send money, or follow instructions in the message. Verify using an official source."