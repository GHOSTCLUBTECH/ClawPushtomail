"""
ClawMail — Email handler
IMAP reading and SMTP sending logic.
"""

import imaplib
import smtplib
import email
import email.header
import email.mime.multipart
import email.mime.text
import email.mime.base
import email.encoders
import re
import time
import logging
from email.utils import parsedate_to_datetime, formataddr
from pathlib import Path

from clawmail.config import (
    IMAP_HOST, IMAP_PORT, SMTP_HOST, SMTP_PORT,
    EMAIL_USER, EMAIL_PASS, EMAIL_NAME,
    ARCHIVE_FOLDER, ATTACHMENT_DIR, EMAIL_SIGNATURE
)

log = logging.getLogger("clawmail")


# ── Header helpers ─────────────────────────────────────────────────────────────

def decode_header_value(value: str) -> str:
    if not value:
        return ""
    parts = email.header.decode_header(value)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(str(part))
    return " ".join(decoded).strip()


def extract_email_address(header_value: str) -> str:
    match = re.search(r'<([^>]+)>', header_value)
    return match.group(1) if match else header_value.strip()


def extract_sender_name(header_value: str) -> str:
    name = header_value.split("<")[0].strip().strip('"').strip("'")
    return name if name else header_value


def escape_html(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ── IMAP ───────────────────────────────────────────────────────────────────────

def connect_imap() -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    imap.login(EMAIL_USER, EMAIL_PASS)
    return imap


def fetch_unread_uids(imap: imaplib.IMAP4_SSL) -> list:
    """Select INBOX and return list of unread UIDs."""
    try:
        status, _ = imap.select("INBOX")
        if status != "OK":
            log.error("Could not select INBOX")
            return []
    except Exception as e:
        log.error(f"IMAP select error: {e}")
        return []

    status, data = imap.search(None, "UNSEEN")
    if status != "OK" or not data[0]:
        return []
    return data[0].split()


def archive_email(imap: imaplib.IMAP4_SSL, uid, uid_str: str):
    """Mark email as read, copy to archive folder, and delete from inbox."""
    imap.store(uid, "+FLAGS", "\\Seen")
    imap.copy(uid, ARCHIVE_FOLDER)
    imap.store(uid, "+FLAGS", "\\Deleted")
    imap.expunge()
    log.info(f"UID {uid_str} archived to {ARCHIVE_FOLDER}")


def parse_email(raw: bytes) -> dict:
    """
    Parse raw email bytes into a structured dict.
    Returns: sender_name, sender_email, subject, body, message_id, received_dt, attachments_data
    """
    from datetime import datetime

    msg = email.message_from_bytes(raw)

    from_header  = msg.get("From", "")
    sender_name  = extract_sender_name(from_header)
    sender_email = extract_email_address(from_header)
    subject      = decode_header_value(msg.get("Subject", "(No Subject)"))
    message_id   = msg.get("Message-ID", "")
    date_str     = msg.get("Date", "")

    try:
        received_dt = parsedate_to_datetime(date_str).strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        received_dt = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # Extract body
    body = ""
    attachments_data = []  # list of (filename, bytes)

    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            filename = part.get_filename()

            if filename:
                filename = decode_header_value(filename)
                payload = part.get_payload(decode=True)
                if payload:
                    attachments_data.append((filename, payload))
            elif ct == "text/plain":
                try:
                    body += part.get_payload(decode=True).decode(
                        part.get_content_charset() or "utf-8", errors="replace"
                    )
                except Exception:
                    pass
    else:
        try:
            body = msg.get_payload(decode=True).decode(
                msg.get_content_charset() or "utf-8", errors="replace"
            )
        except Exception:
            body = ""

    return {
        "sender_name":      sender_name,
        "sender_email":     sender_email,
        "subject":          subject,
        "message_id":       message_id,
        "received_dt":      received_dt,
        "body":             body,
        "attachments_data": attachments_data,
    }


def save_attachments(attachments_data: list) -> list:
    """Save attachment bytes to disk. Returns list of saved Paths."""
    ATTACHMENT_DIR.mkdir(parents=True, exist_ok=True)
    saved = []
    for filename, payload in attachments_data:
        safe_name = re.sub(r'[^\w\.\-]', '_', filename)
        save_path = ATTACHMENT_DIR / safe_name
        if save_path.exists():
            save_path = ATTACHMENT_DIR / f"{save_path.stem}_{int(time.time())}{save_path.suffix}"
        try:
            save_path.write_bytes(payload)
            saved.append(save_path)
            log.info(f"Saved attachment: {save_path.name}")
        except Exception as e:
            log.error(f"Failed to save {filename}: {e}")
    return saved


# ── SMTP ───────────────────────────────────────────────────────────────────────

def send_email(to_address: str, to_name: str, subject: str, body: str,
               in_reply_to: str = None, is_auto_reply: bool = False) -> bool:
    """
    Send an email via SMTP SSL.
    Appends EMAIL_SIGNATURE to body automatically.
    """
    try:
        msg = email.mime.multipart.MIMEMultipart()
        msg["From"]    = formataddr((EMAIL_NAME, EMAIL_USER))
        msg["To"]      = formataddr((to_name, to_address))
        msg["Subject"] = subject if subject.startswith("Re:") else f"Re: {subject}"

        if in_reply_to:
            msg["In-Reply-To"] = in_reply_to
            msg["References"]  = in_reply_to

        if is_auto_reply:
            msg["X-Auto-Response-Suppress"] = "OOF, AutoReply"
            msg["Auto-Submitted"] = "auto-replied"

        full_body = body + EMAIL_SIGNATURE
        msg.attach(email.mime.text.MIMEText(full_body, "plain", "utf-8"))

        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.sendmail(EMAIL_USER, [to_address], msg.as_string())

        log.info(f"Email sent to {to_address} (subject: {subject})")
        return True

    except Exception as e:
        log.error(f"Failed to send email to {to_address}: {e}")
        return False
