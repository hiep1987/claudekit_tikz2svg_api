#!/bin/bash

# VS Code Claude Launcher Script
echo "🚀 Starting Claude Code for VS Code..."

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

# Change to project directory
cd "/Users/hieplequoc/web/work/tikz2svg_api"

# Display configuration
echo "📋 Configuration:"
echo "  • API Base URL: $ANTHROPIC_BASE_URL"
echo "  • API Timeout: $API_TIMEOUT_MS ms"
echo "  • Working Directory: $(pwd)"
echo ""

# Start Claude Code
echo "✨ Launching Claude Code..."
claude "$@"
