# 📝 QUICK FIX: Rate Limit 429 Error

**Issue:** Rate limit bị exceed ngay cả khi chỉ load 6 cards visible  
**Root Cause:** Đang dùng `memory://` storage → Counter chia sẻ giữa tất cả users

---

## ✅ Solution: Setup Redis Storage

### Step 1: Check Redis Installed

```bash
# Check if Redis is running
redis-cli ping
```

**Expected:** `PONG`

**If not installed:**
```bash
sudo apt update
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

---

### Step 2: Add REDIS_URL to .env

```bash
# Backup .env first
sudo cp /var/www/tikz2svg_api/current/.env /var/www/tikz2svg_api/current/.env.backup

# Edit .env
sudo nano /var/www/tikz2svg_api/current/.env
```

**Add this line at the end:**
```env
# Rate Limiting Storage
REDIS_URL=redis://localhost:6379/1
```

**Save and exit:** `Ctrl+X`, then `Y`, then `Enter`

---

### Step 3: Verify .env

```bash
# Check if REDIS_URL was added
grep REDIS_URL /var/www/tikz2svg_api/current/.env

# Expected output:
# REDIS_URL=redis://localhost:6379/1
```

---

### Step 4: Restart Service

```bash
sudo systemctl restart tikz2svg.service
```

---

### Step 5: Verify Redis is Being Used

```bash
# Check logs
sudo journalctl -u tikz2svg.service -n 30 | grep -E "Storage:|Rate Limiting:"

# Expected output:
# 🔧 Rate Limiting: PRODUCTION mode
# 📊 Storage: redis://localhost:6379/1
# ⚡ Limits: {'api_likes_preview': '30 per minute', ...}
```

---

### Step 6: Test in Browser

1. Wait 60 seconds (for old rate limit to expire)
2. Open browser
3. Go to https://tikz2svg.com/
4. Open DevTools Console (F12)
5. Refresh page (Ctrl+Shift+R)

**Expected:**
```
✅ 🔭 Observing 50 file cards for lazy loading
✅ 👁️ Loading likes preview for SVG X (visible)
✅ 200 OK (not 429!)
```

---

## 🎯 Benefits After Fix:

### Before (memory://):
```
❌ Counter shared between all users
❌ Your quota affected by others
❌ 429 errors frequently
```

### After (redis://):
```
✅ Each IP has separate counter
✅ Your quota is yours alone
✅ No 429 errors (unless you really exceed)
```

---

## 📊 Monitoring

### Check Redis is Working:

```bash
# Connect to Redis
redis-cli

# See all keys (rate limit counters)
KEYS *

# Check a specific counter
GET "LIMITER/127.0.0.1/api_likes_preview"

# Exit
exit
```

### Check Rate Limit Status:

```bash
# See how many requests you've made
redis-cli GET "LIMITER/YOUR_IP/api_likes_preview"
```

---

## 🐛 Troubleshooting

### Issue: redis-cli command not found

```bash
# Install Redis
sudo apt update
sudo apt install redis-server redis-tools -y
```

---

### Issue: Cannot connect to Redis

```bash
# Check Redis status
sudo systemctl status redis-server

# If not running, start it
sudo systemctl start redis-server

# Test connection
redis-cli ping
```

---

### Issue: Still getting 429 errors

**Check 1: Verify REDIS_URL in logs**
```bash
sudo journalctl -u tikz2svg.service -n 20 | grep Storage
```

**Check 2: Wait for old rate limit to expire (60 seconds)**

**Check 3: Clear Redis cache**
```bash
redis-cli FLUSHDB
sudo systemctl restart tikz2svg.service
```

---

## ✅ Success Criteria

After fix, you should see:

1. ✅ Logs show: `📊 Storage: redis://localhost:6379/1`
2. ✅ No 429 errors on initial page load
3. ✅ Only 6-8 likes preview API calls (visible cards only)
4. ✅ Can refresh page multiple times without errors

---

**End of Quick Fix Guide** 🎯

