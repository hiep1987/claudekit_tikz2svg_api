# 🚀 QUICK DEPLOY - Rate Limit Fix (500/min)

**Date:** November 1, 2025  
**Commit:** `5ad5831`  
**Issue:** 429 errors after 3 refreshes on VPS

---

## 📊 Changes

### Rate Limits Updated:
- `api_likes_preview`: 150/min → **500/min** ⬆️
- `api_like_counts`: 150/min → **500/min** ⬆️
- `api_general`: 300/min → **1000/min** ⬆️
- `api_write`: 20/min → **50/min** ⬆️

### Why 500/min?
- Lazy loading loads ~20-25 cards per page view
- 500/min = ~20 page refreshes per minute per IP
- Reasonable for real-world usage
- Still protects against abuse

---

## 🔧 VPS Deployment Commands

```bash
# 1. SSH to VPS
ssh hiep1987@your-vps-ip

# 2. Navigate to project
cd /var/www/tikz2svg_api/current

# 3. Pull latest code
git pull origin main

# 4. Verify commit
git log --oneline -1
# Should show: 5ad5831 fix: Increase production rate limits to 500/min

# 5. Restart Gunicorn
sudo systemctl restart tikz2svg.service

# 6. Check status
sudo systemctl status tikz2svg.service

# 7. Check logs for new rate limits
tail -30 /var/www/tikz2svg_api/current/logs/gunicorn_error.log | grep "⚡ Limits"
# Should show: 'api_likes_preview': '500 per minute'

# 8. Clear Redis rate limit counters (optional - fresh start)
redis-cli KEYS "LIMITER*" | xargs redis-cli DEL
```

---

## ✅ Verification

### Test from VPS:
```bash
# Should allow 500 requests per minute from same IP
for i in {1..510}; do 
  curl -s -o /dev/null -w "Request $i: %{http_code}\n" \
  -H "X-Forwarded-For: 1.2.3.4" \
  http://localhost:5000/api/svg/127/likes/preview
done

# Expected:
# Requests 1-500: 200 OK
# Requests 501-510: 429 TOO MANY REQUESTS
```

### Test from Browser:
1. Open `https://tikz2svg.com/`
2. Hard refresh (`Ctrl+Shift+R`)
3. Refresh **10 times** rapidly
4. **Expected:** No 429 errors (10 × 25 cards = 250 requests < 500 limit)

---

## 📈 Rate Limit Calculation

| Action | Cards Loaded | Requests | Limit | Max Refreshes/min |
|--------|--------------|----------|-------|-------------------|
| Page Load | ~25 | 25 | 500 | **20** ✅ |
| Scroll to Bottom | ~25 more | 50 total | 500 | **10** ✅ |
| Full Page Scroll | ~50 | 50 | 500 | **10** ✅ |

---

## 🎯 Expected Results

### Before (150/min):
- ❌ 429 after 3 refreshes (3 × 25 = 75, but with scroll ~150+)
- ❌ Poor UX for active users

### After (500/min):
- ✅ No 429 for normal usage (up to 20 refreshes/min)
- ✅ Still protects against abuse (500 is reasonable limit)
- ✅ Good UX for legitimate users

---

## 🔍 Monitoring

### Check Redis rate limit keys:
```bash
# See all rate limit keys
redis-cli KEYS "LIMITER*"

# Check specific IP's counter
redis-cli GET "LIMITER/api/svg/<id>/likes/preview/<IP_ADDRESS>"

# Monitor in real-time
redis-cli MONITOR | grep LIMITER
```

### Check Gunicorn logs:
```bash
# Real-time monitoring
tail -f /var/www/tikz2svg_api/current/logs/gunicorn_error.log

# Count 429 errors
grep "429" /var/www/tikz2svg_api/current/logs/gunicorn_access.log | wc -l
```

---

## 🚨 If Still Getting 429

### Option 1: Increase limit further
Edit `app.py`:
```python
'api_likes_preview': "1000 per minute"  # Even higher
```

### Option 2: Change to per-hour limit
```python
'api_likes_preview': "5000 per hour"  # More flexible
```

### Option 3: Whitelist specific IPs
Add to `app.py`:
```python
@limiter.request_filter
def ip_whitelist():
    # Skip rate limiting for trusted IPs
    return request.remote_addr in ['1.2.3.4', '5.6.7.8']
```

---

## 📝 Notes

- Development mode: Rate limiting **DISABLED** entirely (`enabled=not IS_DEVELOPMENT`)
- Production mode: Rate limiting **ENABLED** with Redis storage
- Redis ensures consistent rate limiting across multiple Gunicorn workers
- `X-Forwarded-For` header used to get real client IP behind Nginx

---

**Status:** ✅ Ready to deploy  
**Risk:** Low (only increasing limits, not removing protection)  
**Rollback:** Revert to commit `c87e455` if needed

