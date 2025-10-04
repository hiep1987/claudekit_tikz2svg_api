#!/bin/bash

# Script to bypass VS Code extension authentication
echo "🔧 Bypassing VS Code Extension Authentication..."

# Set global environment variables for VS Code
export ANTHROPIC_AUTH_TOKEN="sk-Hkk0lXdFxvOQSjzRoiRc5NG4mCSacATh2LgS6IhwG54OGsZV"
export ANTHROPIC_BASE_URL="https://aishopacc.com"
export ANTHROPIC_MODEL="glm-4.5"
export API_TIMEOUT_MS="600000"

echo "✅ Environment variables set:"
echo "  - API Token: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
echo "  - Base URL: $ANTHROPIC_BASE_URL"
echo "  - Model: $ANTHROPIC_MODEL"

# Option 1: Launch VS Code với extension disabled
echo ""
echo "🚀 Option 1: VS Code without extensions..."
code . --disable-extensions &

# Option 2: Launch VS Code normally (extensions sẽ dùng workspace settings)
sleep 2
echo "🚀 Option 2: VS Code with workspace settings..."
code . &

echo ""
echo "✅ VS Code launched với cả hai options."
echo "💡 Nếu extension vẫn yêu cầu login:"
echo "   1. Dùng terminal (Cmd+\`) và chạy: claude"
echo "   2. Hoặc disable extension trong Extensions tab"
echo "   3. Hoặc copy vscode-user-settings.json vào User Settings"
