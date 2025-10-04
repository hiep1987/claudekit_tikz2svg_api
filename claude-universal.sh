#!/bin/bash

# Universal Claude Script - Hoạt động trong mọi môi trường
# Cursor, VS Code, Terminal thuần

echo "🤖 Claude Universal Launcher"
echo "==========================="

# Detect current environment
if [[ "$TERM_PROGRAM" == "Cursor" ]]; then
    echo "🎯 Detected: Cursor IDE"
    ENVIRONMENT="cursor"
elif [[ "$TERM_PROGRAM" == "vscode" ]]; then
    echo "🎯 Detected: VS Code"
    ENVIRONMENT="vscode"
else
    echo "🎯 Detected: Terminal"
    ENVIRONMENT="terminal"
fi

# Set environment variables
export ANTHROPIC_AUTH_TOKEN="sk-Hkk0lXdFxvOQSjzRoiRc5NG4mCSacATh2LgS6IhwG54OGsZV"
export ANTHROPIC_BASE_URL="https://aishopacc.com"
export CLAUDE_CODE_MAX_OUTPUT_TOKENS="32000"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"
export API_TIMEOUT_MS="600000"
export BASH_DEFAULT_TIMEOUT_MS="600000"
export BASH_MAX_TIMEOUT_MS="600000"
export MCP_TIMEOUT="30000"
export MCP_TOOL_TIMEOUT="600000"
export ANTHROPIC_MODEL="glm-4.5"
export CLAUDE_API_TIMEOUT="600000"

echo ""
echo "✅ Environment configured:"
echo "  • Environment: $ENVIRONMENT"
echo "  • API Token: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
echo "  • Base URL: $ANTHROPIC_BASE_URL"
echo "  • Model: $ANTHROPIC_MODEL"
echo "  • Max Tokens: $CLAUDE_CODE_MAX_OUTPUT_TOKENS"
echo ""

# Check if Claude is available
if command -v claude &> /dev/null; then
    echo "🚀 Starting Claude Code..."
    echo "   Type /help for commands"
    echo "   Type /status to check connection"
    echo "   Type /quit to exit"
    echo ""
    
    # Start Claude with all arguments
    claude "$@"
else
    echo "❌ Claude Code not found!"
    echo ""
    echo "📥 Installation options:"
    echo "   1. npm install -g @anthropic-ai/claude-code"
    echo "   2. curl -fsSL https://claude.ai/install.sh | sh"
    echo ""
    echo "🔍 Current PATH:"
    echo "$PATH" | tr ':' '\n' | sed 's/^/   /'
fi


