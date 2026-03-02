"""
ClawMail — Content filters
Security blocking, auto-reply skip logic, tone detection.
"""

import logging
from clawmail.config import BLOCKED_PATTERNS, SKIP_AUTOREPLY_SENDERS, SKIP_AUTOREPLY_SUBJECTS

log = logging.getLogger("clawmail")


def is_blocked(text: str) -> bool:
    """Return True if email contains sensitive/blocked content (OTPs, card numbers, etc.)."""
    lower = text.lower()
    return any(p in lower for p in BLOCKED_PATTERNS)


def should_skip_autoreply(sender_email: str, sender_name: str, subject: str) -> bool:
    """Return True if this email should NOT receive an auto-reply."""
    sender_lower  = sender_email.lower()
    subject_lower = subject.lower()

    for pattern in SKIP_AUTOREPLY_SENDERS:
        if pattern in sender_lower:
            log.info(f"Auto-reply skipped (sender match: {pattern}): {sender_email}")
            return True

    for pattern in SKIP_AUTOREPLY_SUBJECTS:
        if pattern in subject_lower:
            log.info(f"Auto-reply skipped (subject match: {pattern}): {subject}")
            return True

    return False


def detect_tone(sender_email: str, subject: str, body: str) -> str:
    """
    Detect whether to use 'formal' or 'friendly' tone for auto-reply.
    Returns: 'formal' or 'friendly'
    """
    formal_signals = [
        "director", "manager", "ceo", "cfo", "procurement", "purchase",
        "quotation", "quote", "proposal", "contract", "agreement",
        "partnership", "distribution", "supply", "inquiry", "enquiry",
        "investment", "order", "shipment", ".com", ".ae", ".co",
        "ltd", "llc", "inc", "corp", "group", "trading", "industries"
    ]
    friendly_signals = [
        "gmail.com", "yahoo.com", "hotmail.com", "outlook.com",
        "hey", "hi there", "hope you", "checking in", "just wanted"
    ]

    text = (sender_email + " " + subject + " " + body[:200]).lower()

    formal_score   = sum(1 for s in formal_signals if s in text)
    friendly_score = sum(1 for s in friendly_signals if s in text)

    return "friendly" if friendly_score > formal_score else "formal"
