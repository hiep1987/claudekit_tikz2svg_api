#!/bin/bash
# Clear all Redis rate limit keys

echo "🔍 Checking for LIMITER keys..."
KEYS=$(redis-cli KEYS "LIMITER*")

if [ -z "$KEYS" ]; then
    echo "✅ No LIMITER keys found - Redis is clean"
else
    echo "🗑️ Found LIMITER keys, deleting..."
    redis-cli KEYS "LIMITER*" | xargs -r redis-cli DEL
    echo "✅ All LIMITER keys deleted"
fi

echo ""
echo "📊 Current Redis keys count:"
redis-cli DBSIZE

