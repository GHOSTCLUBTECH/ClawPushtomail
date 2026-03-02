#!/bin/bash
# ClawMail — Quick installer
# Usage: bash scripts/install.sh

set -e

echo "📬 ClawMail Installer"
echo "─────────────────────"

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 is required. Install it first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "✅ Python $PYTHON_VERSION found"

# Install dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt --quiet

# Set up .env
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  Created .env from template."
    echo "   → Edit it now: nano .env"
    echo ""
else
    echo "✅ .env already exists"
fi

# Set up signature
if [ ! -f signature.txt ]; then
    cp signature.txt.example signature.txt
    echo "📝 Created signature.txt — edit it with your details: nano signature.txt"
fi

echo ""
echo "✅ ClawMail is ready!"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your email + Telegram credentials"
echo "  2. Edit signature.txt with your email signature"
echo "  3. Run: python -m clawmail"
echo ""
