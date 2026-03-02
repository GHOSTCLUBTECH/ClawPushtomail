"""
ClawMail — Email summarizer
Extracts a short readable summary from email body text.
"""

import re


def summarize_email(subject: str, body: str, max_chars: int = 800, max_sentences: int = 3) -> str:
    """
    Returns a 1-3 sentence summary of the email body.
    Falls back to truncated body if sentence splitting fails.
    """
    clean = " ".join(body.split())[:max_chars]
    sentences = re.split(r'(?<=[.!?])\s+', clean)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 20][:max_sentences]
    if meaningful:
        return " ".join(meaningful)
    return clean[:300] if clean else "No body content."
