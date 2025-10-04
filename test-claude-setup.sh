#!/bin/bash

echo "🧪 Testing Claude Code Setup..."
echo "================================"

# Set environment variables
export ANTHROPIC_AUTH_TOKEN="sk-Hkk0lXdFxvOQSjzRoiRc5NG4mCSacATh2LgS6IhwG54OGsZV"
export ANTHROPIC_BASE_URL="https://aishopacc.com"
export CLAUDE_CODE_MAX_OUTPUT_TOKENS="32000"
export CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC="1"
export API_TIMEOUT_MS="600000"
export ANTHROPIC_MODEL="glm-4.5"
export CLAUDE_API_TIMEOUT="600000"

echo "✅ Environment variables set:"
echo "  - ANTHROPIC_AUTH_TOKEN: ${ANTHROPIC_AUTH_TOKEN:0:20}..."
echo "  - ANTHROPIC_BASE_URL: $ANTHROPIC_BASE_URL"
echo "  - ANTHROPIC_MODEL: $ANTHROPIC_MODEL"
echo "  - API_TIMEOUT_MS: $API_TIMEOUT_MS"
echo ""

# Test if Claude command exists
if command -v claude &> /dev/null; then
    echo "✅ Claude Code found: $(which claude)"
    echo ""
    
    # Test Claude status
    echo "🔍 Testing Claude status..."
    claude /status 2>&1 || echo "Status check failed"
    echo ""
    
    # Test simple query
    echo "🎯 Testing simple query..."
    echo "Hello, can you respond?" | claude 2>&1 || echo "Query failed"
    
else
    echo "❌ Claude Code not found in PATH"
    echo "   Please install Claude Code first:"
    echo "   npm install -g @anthropic-ai/claude-code"
    echo ""
    echo "📍 Current PATH:"
    echo "$PATH" | tr ':' '\n' | sed 's/^/   /'
fi

echo ""
echo "🏁 Test completed!"
