# Changelog

All notable changes to ClawMail are documented here.
Format: [Semantic Versioning](https://semver.org/)

---

## [1.0.0] — 2026-03-02

### Initial public release

**Features:**
- 📩 IMAP inbox monitoring (IMAP4 SSL)
- 📤 Instant email forwarding to Telegram (HTML formatted)
- 📎 Attachment download + Telegram file forwarding
- 💬 Two-way reply: reply to Telegram notification → sends real email
- 🤖 Smart auto-reply with formal/friendly tone detection
- 🔒 Security filter: blocks OTPs, card numbers from forwarding
- 🗂 Auto-archive processed emails to configurable IMAP folder
- 📝 Fully configurable via `.env` file — zero code changes required
- 🔄 Persistent state across restarts (JSON state file)
- ⚡ Automatic error recovery with exponential back-off

**Architecture:**
- Modular: `config`, `email_handler`, `telegram`, `filters`, `summarizer`, `state`, `agent`
- Installable via pip (`pip install clawmail`)
- Runnable as `clawmail` CLI command or `python -m clawmail`
