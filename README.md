# 📬 ClawMail

> **Turn any email inbox into a Telegram command center.**
> Monitor emails, get instant summaries, reply directly from Telegram — no web browser required.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://python.org)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

---

## What It Does

ClawMail is a lightweight Python agent that runs 24/7 on any server or VPS:

- 📩 **Monitors** your email inbox via IMAP (any cPanel, Gmail, Outlook, custom mail server)
- 📲 **Forwards** new emails to your Telegram — sender, subject, time, and a smart summary
- 📎 **Sends attachments** directly to your Telegram chat
- 💬 **Two-way replies** — reply to any Telegram notification → ClawMail sends a real email back
- 🤖 **Auto-replies** to incoming emails with formal or friendly tone (auto-detected)
- 🔒 **Security filter** — never forwards OTPs, card numbers, or sensitive codes
- 🗂 **Auto-archives** processed emails to a designated IMAP folder

No app. No monthly fee. No vendor lock-in. Just your email, your Telegram, and your server.

---

## Demo

```
📩 New Email

From: John Smith
Email: john@acmecorp.com
Subject: Partnership Inquiry
Time: 2026-03-01 10:32 UTC

Summary: We are interested in exploring a distribution partnership for your
product line across the GCC region. Please find our company profile attached.

💬 Reply to this message to send an email reply back
```

Then you just reply to that Telegram message and ClawMail sends the email. Done.

---

## Quick Start

### 1. Requirements

- Python 3.9+
- A server/VPS (or any machine that runs 24/7)
- An email account with IMAP/SMTP access
- A Telegram bot ([create one free via @BotFather](https://t.me/BotFather))

### 2. Install

```bash
git clone https://github.com/yourusername/clawmail.git
cd clawmail
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install clawmail
```

### 3. Configure

```bash
cp .env.example .env
nano .env   # Fill in your credentials
```

Minimum required settings:

```env
IMAP_HOST=mail.yourdomain.com
SMTP_HOST=mail.yourdomain.com
EMAIL_USER=you@yourdomain.com
EMAIL_PASS=your_password
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

> **How to get your Telegram Chat ID:** Message [@userinfobot](https://t.me/userinfobot) on Telegram — it'll reply with your chat ID.

### 4. Add your signature (optional)

```bash
cp signature.txt.example signature.txt
nano signature.txt   # Write your email signature
```

### 5. Run

```bash
python -m clawmail
```

Or if installed via pip:

```bash
clawmail
```

---

## Running as a Background Service

### Option A: systemd (recommended for Linux VPS)

```ini
# /etc/systemd/system/clawmail.service
[Unit]
Description=ClawMail Email Agent
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/clawmail
ExecStart=/usr/bin/python3 -m clawmail
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/clawmail/.env

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable clawmail
sudo systemctl start clawmail
sudo systemctl status clawmail
```

### Option B: screen / tmux

```bash
screen -S clawmail
python -m clawmail
# Ctrl+A, D to detach
```

### Option C: nohup

```bash
nohup python -m clawmail > clawmail.log 2>&1 &
```

---

## Configuration Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `IMAP_HOST` | ✅ | — | IMAP server hostname |
| `SMTP_HOST` | ✅ | — | SMTP server hostname |
| `IMAP_PORT` | | `993` | IMAP SSL port |
| `SMTP_PORT` | | `465` | SMTP SSL port |
| `EMAIL_USER` | ✅ | — | Your email address |
| `EMAIL_PASS` | ✅ | — | Email password |
| `EMAIL_NAME` | | `EMAIL_USER` | Display name for outgoing emails |
| `TELEGRAM_BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `TELEGRAM_CHAT_ID` | ✅ | — | Your Telegram chat ID |
| `POLL_INTERVAL` | | `60` | Seconds between inbox checks |
| `ARCHIVE_FOLDER` | | `INBOX.FORWARDED` | IMAP folder to archive processed emails |
| `ATTACHMENT_DIR` | | `~/ClawMail` | Local directory to save attachments |
| `EMAIL_SIGNATURE_FILE` | | — | Path to a `.txt` file with your email signature |
| `EMAIL_SIGNATURE` | | — | Inline signature (alternative to file) |

---

## Compatibility

Works with any IMAP/SMTP mail server:

| Provider | IMAP Host | Notes |
|---|---|---|
| cPanel / Hosting | `mail.yourdomain.com` | Standard setup |
| Gmail | `imap.gmail.com` | Requires App Password |
| Outlook / Office 365 | `outlook.office365.com` | SMTP: `smtp.office365.com` |
| Zoho Mail | `imap.zoho.com` | |
| Custom / Self-hosted | Your server | |

---

## Architecture

```
clawmail/
├── __init__.py       Version info
├── __main__.py       Entry point
├── agent.py          Core orchestration loop
├── config.py         Configuration loader (.env → typed values)
├── email_handler.py  IMAP reading + SMTP sending
├── telegram.py       Telegram Bot API client
├── filters.py        Security + auto-reply skip logic + tone detection
├── summarizer.py     Email body → short summary
└── state.py          JSON state persistence
```

---

## Security

- Credentials are loaded from `.env` — never hardcoded
- Add `.env` to `.gitignore` — **never commit credentials**
- Built-in security filter blocks OTPs, card numbers, and verification codes from being forwarded
- Only processes messages from your configured `TELEGRAM_CHAT_ID`
- Emails are archived (not deleted) after processing — fully recoverable

---

## Customization

ClawMail is designed to be modified. Common customizations:

**Custom auto-reply templates** — edit `AUTO_REPLY_FORMAL` and `AUTO_REPLY_FRIENDLY` in `agent.py`

**Custom security rules** — add patterns to `BLOCKED_PATTERNS` in `config.py`

**Custom skip rules** — add sender/subject patterns to `SKIP_AUTOREPLY_SENDERS` / `SKIP_AUTOREPLY_SUBJECTS`

**Custom summary logic** — edit `summarizer.py` (plug in an LLM here for better summaries)

**Multiple inboxes** — run multiple instances with different `.env` files

---

## Contributing

Pull requests welcome. Please open an issue first for major changes.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'Add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## License

MIT — free to use, modify, and distribute. See [LICENSE](LICENSE).

---

## Support

- 🐛 **Bug reports:** [GitHub Issues](https://github.com/yourusername/clawmail/issues)
- 💬 **Questions:** [GitHub Discussions](https://github.com/yourusername/clawmail/discussions)

---

*Built with ❤️ — simple tools for people who live in their inbox.*
