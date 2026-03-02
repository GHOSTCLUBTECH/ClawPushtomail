"""
ClawMail — Telegram integration
Sending messages, files, and polling for updates.
"""

import requests
import logging
from pathlib import Path
from clawmail.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

log = logging.getLogger("clawmail")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


def send_message(text: str, reply_markup=None) -> dict:
    """Send a text message to the configured Telegram chat."""
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    r = requests.post(f"{BASE_URL}/sendMessage", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()


def send_file(file_path: Path, caption: str = "") -> dict:
    """Send a file/document to the configured Telegram chat."""
    url = f"{BASE_URL}/sendDocument"
    with open(file_path, "rb") as f:
        r = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption},
            files={"document": (file_path.name, f)},
            timeout=60
        )
    r.raise_for_status()
    return r.json()


def get_updates(offset=None) -> dict:
    """Long-poll Telegram for new messages."""
    params = {"timeout": 30, "allowed_updates": ["message"]}
    if offset:
        params["offset"] = offset
    try:
        r = requests.get(f"{BASE_URL}/getUpdates", params=params, timeout=40)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        log.error(f"Failed to get Telegram updates: {e}")
        return {"ok": False, "result": []}
