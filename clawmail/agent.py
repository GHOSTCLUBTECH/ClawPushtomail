"""
ClawMail — Core Agent
Orchestrates email polling, Telegram forwarding, auto-replies, and reply handling.
"""

import time
import threading
import logging
import imaplib
import requests

from clawmail import config
from clawmail.state import load_state, save_state
from clawmail.filters import is_blocked, should_skip_autoreply, detect_tone
from clawmail.summarizer import summarize_email
from clawmail.email_handler import (
    connect_imap, fetch_unread_uids, parse_email,
    save_attachments, archive_email, send_email, escape_html
)
from clawmail import telegram

log = logging.getLogger("clawmail")

# ── Auto-reply templates ───────────────────────────────────────────────────────

AUTO_REPLY_FORMAL = """Dear {sender_name},

Thank you for your email. This message confirms that your correspondence has been received.

Your message will be reviewed and responded to within 1–2 business days. If your matter is urgent, please resend with "URGENT" in the subject line.

Best regards,"""

AUTO_REPLY_FRIENDLY = """Hi {sender_name},

Thanks for reaching out! Just a quick note to let you know your email has been received.

We'll get back to you as soon as possible — usually within 1–2 business days. If it's urgent, feel free to resend with URGENT in the subject line.

Speak soon!"""


def send_auto_reply(sender_email, sender_name, subject, tone, message_id=None):
    if tone == "friendly":
        first_name = sender_name.split()[0] if sender_name else "there"
        body = AUTO_REPLY_FRIENDLY.format(sender_name=first_name)
    else:
        body = AUTO_REPLY_FORMAL.format(sender_name=sender_name or "Sir/Madam")

    return send_email(
        to_address=sender_email,
        to_name=sender_name,
        subject=subject,
        body=body,
        in_reply_to=message_id,
        is_auto_reply=True
    )


# ── Email processing ───────────────────────────────────────────────────────────

def process_email(imap, uid, state):
    uid_str = uid.decode() if isinstance(uid, bytes) else str(uid)

    if uid_str in state["processed_ids"]:
        return

    status, data = imap.fetch(uid, "(RFC822)")
    if status != "OK":
        log.error(f"Failed to fetch UID {uid_str}")
        return

    raw = data[0][1]
    parsed = parse_email(raw)

    sender_name  = parsed["sender_name"]
    sender_email = parsed["sender_email"]
    subject      = parsed["subject"]
    message_id   = parsed["message_id"]
    received_dt  = parsed["received_dt"]
    body         = parsed["body"]
    attachments_data = parsed["attachments_data"]

    # Security check
    if is_blocked(subject + " " + body):
        log.warning(f"UID {uid_str} blocked by security filter.")
        imap.store(uid, "+FLAGS", "\\Seen")
        state["processed_ids"].append(uid_str)
        save_state(state)
        return

    summary = summarize_email(subject, body)
    saved_attachments = save_attachments(attachments_data)

    # Build and send Telegram notification
    telegram_text = (
        f"📩 <b>New Email</b>\n\n"
        f"<b>From:</b> {escape_html(sender_name)}\n"
        f"<b>Email:</b> <code>{escape_html(sender_email)}</code>\n"
        f"<b>Subject:</b> {escape_html(subject)}\n"
        f"<b>Time:</b> {received_dt}\n\n"
        f"<b>Summary:</b>\n{escape_html(summary)}\n\n"
        f"💬 <i>Reply to this message to send an email reply back</i>"
    )

    try:
        result = telegram.send_message(telegram_text)
        tg_msg_id = str(result["result"]["message_id"])
        state["telegram_msg_map"][tg_msg_id] = {
            "sender_email": sender_email,
            "sender_name":  sender_name,
            "subject":      subject,
            "message_id":   message_id
        }
        log.info(f"Telegram message sent (msg_id={tg_msg_id}) for UID {uid_str}")
    except Exception as e:
        log.error(f"Failed to send Telegram message: {e}")
        return

    # Auto-reply
    if not should_skip_autoreply(sender_email, sender_name, subject):
        tone = detect_tone(sender_email, subject, body)
        send_auto_reply(sender_email, sender_name, subject, tone, message_id)

    # Forward attachments to Telegram
    for att_path in saved_attachments:
        try:
            telegram.send_file(att_path, caption=f"📎 {att_path.name}")
            log.info(f"Attachment sent: {att_path.name}")
        except Exception as e:
            log.error(f"Failed to send attachment {att_path.name}: {e}")
            try:
                telegram.send_message(f"⚠️ Attachment upload failed: {att_path.name}")
            except Exception:
                pass

    # Archive email
    try:
        archive_email(imap, uid, uid_str)
    except Exception as e:
        log.error(f"Failed to archive UID {uid_str}: {e}")

    # Update state
    state["processed_ids"].append(uid_str)
    if len(state["processed_ids"]) > 1000:
        state["processed_ids"] = state["processed_ids"][-500:]
    save_state(state)


# ── Telegram reply listener ────────────────────────────────────────────────────

def telegram_reply_listener(state):
    """
    Background thread: long-polls Telegram and handles replies from the user.
    A Telegram reply to a forwarded email → sends an actual email reply.
    """
    log.info("Telegram reply listener started.")
    offset = state.get("telegram_offset")

    while True:
        try:
            data = telegram.get_updates(offset)
            if not data.get("ok"):
                time.sleep(5)
                continue

            for update in data.get("result", []):
                offset = update["update_id"] + 1
                state["telegram_offset"] = offset

                msg = update.get("message", {})
                if not msg:
                    continue

                # Only accept messages from the configured chat
                chat_id = str(msg.get("chat", {}).get("id", ""))
                if chat_id != config.TELEGRAM_CHAT_ID:
                    continue

                text = msg.get("text", "").strip()
                if not text:
                    continue

                reply_to = msg.get("reply_to_message", {})
                if not reply_to:
                    continue  # Not a reply — ignore

                replied_msg_id = str(reply_to.get("message_id", ""))
                email_meta = state["telegram_msg_map"].get(replied_msg_id)

                if not email_meta:
                    telegram.send_message(
                        "⚠️ Could not find the original email for this reply.\n"
                        "Please reply directly to the email summary message."
                    )
                    save_state(state)
                    continue

                success = send_email(
                    to_address=email_meta["sender_email"],
                    to_name=email_meta["sender_name"],
                    subject=email_meta["subject"],
                    body=text,
                    in_reply_to=email_meta.get("message_id", "")
                )

                if success:
                    telegram.send_message(
                        f"✅ <b>Reply sent!</b>\n\n"
                        f"<b>To:</b> {escape_html(email_meta['sender_name'])} "
                        f"&lt;{escape_html(email_meta['sender_email'])}&gt;\n"
                        f"<b>Subject:</b> Re: {escape_html(email_meta['subject'])}"
                    )
                else:
                    telegram.send_message(
                        f"❌ Failed to send reply to {escape_html(email_meta['sender_email'])}. "
                        f"Please try again."
                    )

            save_state(state)

        except Exception as e:
            log.error(f"Reply listener error: {e}")
            time.sleep(10)


# ── Main loop ──────────────────────────────────────────────────────────────────

def run():
    """Start the ClawMail agent (email poller + Telegram reply listener)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [ClawMail] %(levelname)s — %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(config.ATTACHMENT_DIR.parent / "clawmail.log"),
        ]
    )

    log.info("🚀 ClawMail starting...")
    config.ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)

    state = load_state()
    if "telegram_msg_map" not in state:
        state["telegram_msg_map"] = {}

    # Start reply listener thread
    reply_thread = threading.Thread(
        target=telegram_reply_listener, args=(state,), daemon=True
    )
    reply_thread.start()

    # Startup notification
    try:
        telegram.send_message(
            f"🟢 <b>ClawMail Active</b>\n\n"
            f"📥 Monitoring: <code>{config.EMAIL_USER}</code>\n"
            f"⏱ Poll interval: {config.POLL_INTERVAL}s\n"
            f"💬 Reply to any message to send an email reply\n\n"
            f"Ready 🚀"
        )
    except Exception as e:
        log.error(f"Startup notification failed: {e}")

    consecutive_errors = 0

    while True:
        try:
            imap = connect_imap()
            uids = fetch_unread_uids(imap)

            if uids:
                log.info(f"Found {len(uids)} unread email(s)")
                for uid in uids:
                    process_email(imap, uid, state)
            else:
                log.info("No new emails.")

            try:
                imap.logout()
            except Exception:
                pass

            consecutive_errors = 0

        except imaplib.IMAP4.error as e:
            log.error(f"IMAP error: {e}")
            consecutive_errors += 1
        except requests.exceptions.ConnectionError:
            log.warning("No internet. Retrying...")
            consecutive_errors += 1
        except Exception as e:
            log.error(f"Unexpected error: {e}")
            consecutive_errors += 1

        if consecutive_errors >= 5:
            log.critical("5 consecutive errors — pausing 5 minutes")
            time.sleep(300)
            consecutive_errors = 0

        time.sleep(config.POLL_INTERVAL)
