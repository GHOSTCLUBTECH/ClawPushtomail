"""
ClawMail — State persistence
Handles loading/saving of processed IDs, Telegram message map, and offset.
"""

import json
import logging
from clawmail.config import STATE_FILE

log = logging.getLogger("clawmail")

def load_state():
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Failed to load state: {e}")
    return {"processed_ids": [], "telegram_msg_map": {}, "telegram_offset": None}

def save_state(state):
    try:
        with open(STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        log.error(f"Failed to save state: {e}")
