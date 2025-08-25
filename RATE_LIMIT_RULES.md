# 🚦 Rate Limit Rules (Email)

## 1) Global counters (in-memory)
- hourly_count: đếm số email đã gửi trong 1 giờ gần nhất
- daily_count: đếm số email đã gửi trong 24 giờ gần nhất
- last_hour_reset: mốc thời gian reset theo giờ
- last_day_reset: mốc thời gian reset theo ngày
- last_email_time: thời gian gửi email gần nhất (dùng cho cooldown)

Nguồn: `email_service.EmailService.rate_limit_data`

## 2) Reset counters
- Reset theo giờ: nếu `now - last_hour_reset > 1 giờ` → `hourly_count = 0`, cập nhật `last_hour_reset = now`
- Reset theo ngày: nếu `now - last_day_reset > 1 ngày` → `daily_count = 0`, cập nhật `last_day_reset = now`

Nguồn: `EmailService._check_rate_limit()`

## 3) Cooldown giữa các lần gửi
- Nếu có `last_email_time` và `now - last_email_time < cooldown_minutes` → chặn gửi
- Cooldown (phút) lấy từ cấu hình `EMAIL_RATE_LIMIT['cooldown_minutes']`

Nguồn: `email_config.EMAIL_RATE_LIMIT`, `EmailService._check_rate_limit()`

## 4) Giới hạn theo giờ/ngày
- Nếu `hourly_count >= max_emails_per_hour` → chặn gửi
- Nếu `daily_count >= max_emails_per_day` → chặn gửi
- Các giá trị lấy từ `EMAIL_RATE_LIMIT` (config)

Nguồn: `email_config.EMAIL_RATE_LIMIT`, `EmailService._check_rate_limit()`

## 5) Cập nhật counters sau khi gửi thành công
- `hourly_count += 1`
- `daily_count += 1`
- `last_email_time = now`

Nguồn: `EmailService._update_rate_limit()` (gọi sau khi `self.mail.send(msg)` thành công)

## 6) Bypass rate limit (Development/Test)
- Tham số: `bypass_rate_limit: bool = False` trong `EmailService.send_email(...)`
- Khi `bypass_rate_limit=True` → bỏ qua `_check_rate_limit()` và vẫn gửi
- Dùng cho: API test (`/api/test-email-direct`), email-test page

Nguồn: `EmailService.send_email()` và routes test trong `app.py`

## 7) Logging & phản hồi khi bị chặn
- In console:
  - "Rate limit: Cooldown active, X minutes remaining"
  - "Rate limit: Hourly limit reached (h/m)" hoặc "Daily limit reached (d/M)"
  - "Rate limit exceeded for email to <recipient>"
- Ghi vào bảng `email_log` với `success=0` và `error_message='Rate limit exceeded'` khi bị chặn (nếu dùng nhánh kiểm tra có logging)

Nguồn: `EmailService._check_rate_limit()`, `EmailService.send_email()`

## 8) Cấu hình tham chiếu
```python
# email_config.py
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 100,   # Dev mặc định hiện tại (có thể đổi bằng script)
    'max_emails_per_day': 1000,   # Dev mặc định hiện tại (có thể đổi bằng script)
    'cooldown_minutes': 1         # Dev mặc định hiện tại (có thể đổi bằng script)
}
```
- Production khuyến nghị: `50/hour`, `500/day`, `cooldown_minutes=5`
- Dùng script chuyển đổi nhanh: `python switch_rate_limit_mode.py dev|prod|show|reset`

## 9) Áp dụng/Phạm vi
- Rate limit áp dụng cho mọi thao tác gửi email qua `EmailService.send_email()`
- Bao gồm tất cả templates: `welcome`, `account_verification`, `profile_settings_verification`, `svg_verification`, `notification`, ...
- Các route/procedure custom có thể bật bypass khi test/development

## 10) Lưu ý kiến trúc
- Rate limit counters đang lưu in-memory (mất khi app restart)
- Với production có nhu cầu nghiêm ngặt: nên chuyển sang store phân tán (Redis) hoặc ghi DB

## 11) Cách kiểm thử nhanh
- Bypass: `python test_email_bypass_rate_limit.py`
- Không bypass (thực tế): `python test_rate_limit_real.py`
- Reset counters: `python reset_rate_limit.py`
- Kiểm tra config: `python switch_rate_limit_mode.py show`

## 12) Troubleshooting nhanh
- Thấy bị chặn ngay: kiểm tra cooldown còn lại
- Không bao giờ bị chặn: có thể đang bật bypass hoặc counters reset do app restart
- Log DB không thấy: kiểm tra kết nối DB trong `EmailService._log_email_sent()`

## 13) SVG daily save limit (yêu cầu xác thực trước khi lưu tiếp)
- Quy tắc: Mỗi user chỉ được lưu tối đa N file SVG mỗi ngày. Khi vượt ngưỡng, hệ thống gửi email xác thực (template `svg_verification`) và yêu cầu nhập mã trước khi cho phép lưu tiếp.
- Ngưỡng: `SVG_VERIFICATION_CONFIG['daily_svg_limit']`
- Cấu hình qua env: `DAILY_SVG_LIMIT` (mặc định 10 nếu không set)
- Template email: `templates/emails/svg_verification.html`
- Context chính: `verification_code`, `svg_name`, `svg_width`, `svg_height`, `svg_size`, `daily_limit`, `verification_url`
- Vị trí logic: trong các route xử lý lưu SVG (gọi email_service gửi `svg_verification` khi đụng ngưỡng)
- Test nhanh:
  - Gửi trực tiếp: `python test_svg_verification_email.py`
  - Qua API test: `python test_all_email_templates.py` (case `svg_verification`)
- Gợi ý prod: đặt `DAILY_SVG_LIMIT` phù hợp tải hệ thống và hành vi người dùng.
