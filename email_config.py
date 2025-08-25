"""
Cấu hình email cho Zoho Mail SMTP
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Cấu hình SMTP Zoho Mail
ZOHO_MAIL_CONFIG = {
    'MAIL_SERVER': 'smtp.zoho.com',
    'MAIL_PORT': 587,  # TLS port
    'MAIL_USE_TLS': True,
    'MAIL_USE_SSL': False,
    'MAIL_USERNAME': os.environ.get('ZOHO_EMAIL', 'support@tikz2svg.com'),
    'MAIL_PASSWORD': os.environ.get('ZOHO_APP_PASSWORD', 'your-app-password'),
    'MAIL_DEFAULT_SENDER': (
        f"{os.environ.get('MAIL_SENDER_NAME', os.environ.get('APP_NAME', 'TikZ2SVG'))} <{os.environ.get('ZOHO_EMAIL', 'support@tikz2svg.com')}>"
    ),
    'MAIL_MAX_EMAILS': 10,  # Giới hạn số email gửi mỗi lần
    'MAIL_ASCII_ATTACHMENTS': False,
    'MAIL_SUPPRESS_SEND': False,  # Set True để test mode (không gửi thật)
}

# Cấu hình email templates
EMAIL_TEMPLATES = {
    'welcome': {
        'subject': 'Chào mừng bạn đến với TikZ2SVG API',
        'template': 'emails/welcome.html'
    },
    'account_verification': {
        'subject': 'Xác thực tài khoản - TikZ2SVG API',
        'template': 'emails/account_verification.html'
    },
    'svg_verification': {
        'subject': 'Xác thực lưu file SVG - TikZ2SVG API',
        'template': 'emails/svg_verification.html'
    },
    'password_reset': {
        'subject': 'Đặt lại mật khẩu - TikZ2SVG API',
        'template': 'emails/password_reset.html'
    },
    'svg_shared': {
        'subject': 'SVG được chia sẻ với bạn - TikZ2SVG API',
        'template': 'emails/svg_shared.html'
    },
    'notification': {
        'subject': 'Thông báo mới - TikZ2SVG API',
        'template': 'emails/notification.html'
    },
    'profile_settings_verification': {
        'subject': 'Xác thực thay đổi hồ sơ - TikZ2SVG API',
        'template': 'emails/profile_settings_verification.html'
    }
}

# Danh sách email admin
ADMIN_EMAILS = [
    os.environ.get('ADMIN_EMAIL', 'admin@yourdomain.com')
]

# Cấu hình rate limiting cho email
EMAIL_RATE_LIMIT = {
    'max_emails_per_hour': 100,  # Tăng giới hạn cho development
    'max_emails_per_day': 1000,  # Tăng giới hạn cho development
    'cooldown_minutes': 1  # Giảm thời gian chờ cho development (từ 5 phút xuống 1 phút)
}

# Cấu hình xác thực SVG
SVG_VERIFICATION_CONFIG = {
    'daily_svg_limit': int(os.environ.get('DAILY_SVG_LIMIT', 10)),  # Số file SVG tối đa/ngày trước khi cần xác thực
    'verification_code_expiry_hours': 24,  # Thời gian hết hạn mã xác thực
    'verification_code_length': 6  # Độ dài mã xác thực
}
