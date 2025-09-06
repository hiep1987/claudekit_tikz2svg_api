#!/bin/bash

# Script để chạy Claude với custom API endpoint
export ANTHROPIC_AUTH_TOKEN=sk-HQ9CGnvN5Ov2hx98wUhbZ2hZyLef1Q9BnJtheL7wEGod5giY
export ANTHROPIC_BASE_URL=https://poloai.top
export API_TIMEOUT_MS=300000

# Chạy Claude với environment variables
claude "$@"
