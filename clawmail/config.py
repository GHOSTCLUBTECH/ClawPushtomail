"""
ClawMail — Configuration loader
Reads from .env file or environment variables.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from current working directory or home
load_dotenv(Path.cwd() / ".env")
load_dotenv(Path.home() / ".clawmail.env")

def _require(key):
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"[ClawMail] Missing required config: {key}\n"
            f"  → Set it in your .env file. See .env.example for reference."
        )
    return val

# ── Email ──────────────────────────────────────────────────────────────────────
IMAP_HOST   = _require("IMAP_HOST")
SMTP_HOST   = _require("SMTP_HOST")
IMAP_PORT   = int(os.getenv("IMAP_PORT", "993"))
SMTP_PORT   = int(os.getenv("SMTP_PORT", "465"))
EMAIL_USER  = _require("EMAIL_USER")
EMAIL_PASS  = _require("EMAIL_PASS")
EMAIL_NAME  = os.getenv("EMAIL_NAME", EMAIL_USER)

# ── Telegram ───────────────────────────────────────────────────────────────────
TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = _require("TELEGRAM_CHAT_ID")

# ── Behavior ───────────────────────────────────────────────────────────────────
POLL_INTERVAL  = int(os.getenv("POLL_INTERVAL", "60"))
ARCHIVE_FOLDER = os.getenv("ARCHIVE_FOLDER", "INBOX.FORWARDED")
ATTACHMENT_DIR = Path(os.path.expanduser(os.getenv("ATTACHMENT_DIR", "~/ClawMail")))
STATE_FILE     = Path(os.path.expanduser(os.getenv("STATE_FILE", "~/.clawmail_state.json")))

# ── Signature ──────────────────────────────────────────────────────────────────
_sig_file = os.getenv("EMAIL_SIGNATURE_FILE")
if _sig_file and Path(_sig_file).exists():
    EMAIL_SIGNATURE = "\n\n--\n" + Path(_sig_file).read_text().strip()
elif os.getenv("EMAIL_SIGNATURE"):
    EMAIL_SIGNATURE = "\n\n--\n" + os.getenv("EMAIL_SIGNATURE").strip()
else:
    EMAIL_SIGNATURE = ""

# ── Security: blocked content patterns ────────────────────────────────────────
BLOCKED_PATTERNS = [
    "otp", "one-time password", "verification code", "your code is",
    "card number", "cvv", "credit card", "debit card"
]

# ── Auto-reply: skip these senders ────────────────────────────────────────────
SKIP_AUTOREPLY_SENDERS = [
    "noreply", "no-reply", "donotreply", "do-not-reply", "do_not_reply",
    "notifications", "newsletter", "marketing", "promo", "promotions",
    "updates", "mailer", "automailer", "bulk", "digest", "alerts",
    "support@", "helpdesk", "billing", "invoices", "statements",
    "accounts@", "accountspayable", "finance@", "statement@",
    "unsubscribe", "bounce", "postmaster", "mailer-daemon"
]

# ── Auto-reply: skip these subjects ───────────────────────────────────────────
SKIP_AUTOREPLY_SUBJECTS = [
    "invoice", "statement", "receipt", "payment confirmation",
    "order confirmation", "your order", "subscription", "unsubscribe",
    "newsletter", "weekly digest", "monthly digest", "out of office",
    "auto-reply", "automatic reply", "automated response", "do not reply",
    "no reply", "delivery report", "delivery status", "mail delivery",
    "delivery failed", "failure notice", "returned mail", "bounce",
    "verification", "confirm your email", "activate your account",
    "special offer", "limited time", "sale ends", "discount", "deal",
    "% off", "free shipping", "unsubscribe"
]
