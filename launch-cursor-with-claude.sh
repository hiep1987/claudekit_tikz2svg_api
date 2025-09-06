#!/bin/bash

# Script để launch Cursor/VS Code với Claude environment variables
export ANTHROPIC_AUTH_TOKEN=sk-HQ9CGnvN5Ov2hx98wUhbZ2hZyLef1Q9BnJtheL7wEGod5giY
export ANTHROPIC_BASE_URL=https://poloai.top
export API_TIMEOUT_MS=300000

# Launch Cursor với environment variables
if command -v cursor &> /dev/null; then
    echo "Launching Cursor with Claude custom API..."
    cursor "$@"
elif command -v code &> /dev/null; then
    echo "Launching VS Code with Claude custom API..."
    code "$@"
else
    echo "Neither Cursor nor VS Code found"
    exit 1
fi
