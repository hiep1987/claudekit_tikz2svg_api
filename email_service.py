"""
Email Service cho TikZ2SVG API
Sử dụng Flask-Mail với Zoho SMTP
"""

import os
import time
import threading
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from flask import Flask, render_template, url_for
from flask_mail import Mail, Message
from email_config import ZOHO_MAIL_CONFIG, EMAIL_TEMPLATES, ADMIN_EMAILS, EMAIL_RATE_LIMIT, SVG_VERIFICATION_CONFIG
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class EmailService:
    def __init__(self, app: Flask):
        self.app = app
        self.mail = None
        self.rate_limit_data = {
            'hourly_count': 0,
            'daily_count': 0,
            'last_hour_reset': datetime.now(),
            'last_day_reset': datetime.now(),
            'last_email_time': None
        }
        self._setup_mail()
    
    def _setup_mail(self):
        """Thiết lập Flask-Mail với cấu hình Zoho"""
        self.app.config.update(ZOHO_MAIL_CONFIG)
        self.mail = Mail(self.app)
    
    def _check_rate_limit(self) -> bool:
        """Kiểm tra rate limiting cho email"""
        now = datetime.now()
        
        # Reset counters nếu cần
        if now - self.rate_limit_data['last_hour_reset'] > timedelta(hours=1):
            self.rate_limit_data['hourly_count'] = 0
            self.rate_limit_data['last_hour_reset'] = now
        
        if now - self.rate_limit_data['last_day_reset'] > timedelta(days=1):
            self.rate_limit_data['daily_count'] = 0
            self.rate_limit_data['last_day_reset'] = now
        
        # Kiểm tra cooldown
        if (self.rate_limit_data['last_email_time'] and 
            now - self.rate_limit_data['last_email_time'] < timedelta(minutes=EMAIL_RATE_LIMIT['cooldown_minutes'])):
            remaining_time = EMAIL_RATE_LIMIT['cooldown_minutes'] - (now - self.rate_limit_data['last_email_time']).total_seconds() / 60
            print(f"Rate limit: Cooldown active, {remaining_time:.1f} minutes remaining", flush=True)
            return False
        
        # Kiểm tra giới hạn
        if self.rate_limit_data['hourly_count'] >= EMAIL_RATE_LIMIT['max_emails_per_hour']:
            print(f"Rate limit: Hourly limit reached ({self.rate_limit_data['hourly_count']}/{EMAIL_RATE_LIMIT['max_emails_per_hour']})", flush=True)
            return False
        
        if self.rate_limit_data['daily_count'] >= EMAIL_RATE_LIMIT['max_emails_per_day']:
            print(f"Rate limit: Daily limit reached ({self.rate_limit_data['daily_count']}/{EMAIL_RATE_LIMIT['max_emails_per_day']})", flush=True)
            return False
        
        return True
    
    def _update_rate_limit(self):
        """Cập nhật rate limit counters"""
        self.rate_limit_data['hourly_count'] += 1
        self.rate_limit_data['daily_count'] += 1
        self.rate_limit_data['last_email_time'] = datetime.now()
    
    def _log_email_sent(self, recipient: str, template: str, success: bool, error: str = None):
        """Log việc gửi email vào database"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO email_log (recipient, template, success, error_message, sent_at)
                VALUES (%s, %s, %s, %s, %s)
            """, (recipient, template, success, error, datetime.now()))
            
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print(f"Error logging email: {e}", flush=True)
    
    def send_email(self, 
                   recipient: str, 
                   template_name: str, 
                   subject: str = None, 
                   context: Dict = None,
                   attachments: List = None,
                   bypass_rate_limit: bool = False) -> bool:
        """
        Gửi email sử dụng template
        
        Args:
            recipient: Email người nhận
            template_name: Tên template (welcome, password_reset, etc.)
            subject: Tiêu đề email (nếu không có sẽ dùng từ template)
            context: Dữ liệu context cho template
            attachments: Danh sách file đính kèm
        
        Returns:
            bool: True nếu gửi thành công, False nếu thất bại
        """
        # Kiểm tra rate limiting (trừ khi bypass)
        if not bypass_rate_limit and not self._check_rate_limit():
            print(f"Rate limit exceeded for email to {recipient}", flush=True)
            self._log_email_sent(recipient, template_name, False, "Rate limit exceeded")
            return False
        
        if context is None:
            context = {}
        
        # Lấy thông tin template
        template_info = EMAIL_TEMPLATES.get(template_name)
        if not template_info:
            print(f"Template {template_name} not found", flush=True)
            return False
        
        # Sử dụng subject từ template nếu không có
        if not subject:
            subject = template_info['subject']
        
        try:
            with self.app.app_context():
                # Render template
                html_content = render_template(template_info['template'], **context)
                
                # Tạo message
                msg = Message(
                    subject=subject,
                    recipients=[recipient],
                    html=html_content
                )
                
                # Thêm attachments nếu có
                if attachments:
                    for attachment in attachments:
                        if isinstance(attachment, tuple) and len(attachment) >= 2:
                            filename, file_data, content_type = attachment[0], attachment[1], attachment[2] if len(attachment) > 2 else None
                            msg.attach(filename, content_type or 'application/octet-stream', file_data)
                
                # Gửi email
                self.mail.send(msg)
                
                # Cập nhật rate limit
                self._update_rate_limit()
                
                # Log thành công
                self._log_email_sent(recipient, template_name, True)
                
                print(f"Email sent successfully to {recipient} using template {template_name}", flush=True)
                return True
                
        except Exception as e:
            error_msg = str(e)
            print(f"Error sending email to {recipient}: {error_msg}", flush=True)
            
            # Log lỗi
            self._log_email_sent(recipient, template_name, False, error_msg)
            return False
    
    def send_welcome_email(self, email: str, username: str) -> bool:
        """Gửi email chào mừng cho user mới"""
        context = {
            'username': username,
            'email': email,
            'app_url': os.environ.get('APP_URL', 'https://yourdomain.com')
        }
        return self.send_email(email, 'welcome', context=context)
    
    def send_password_reset_email(self, email: str, username: str, reset_token: str) -> bool:
        """Gửi email đặt lại mật khẩu"""
        reset_url = f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/reset-password?token={reset_token}"
        context = {
            'username': username,
            'email': email,
            'reset_url': reset_url,
            'expiry_hours': 24
        }
        return self.send_email(email, 'password_reset', context=context)
    
    def send_account_verification_email(self, email: str, username: str, verification_code: str) -> bool:
        """Gửi email xác thực tài khoản"""
        verification_url = f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/verify-account?code={verification_code}"
        context = {
            'username': username,
            'email': email,
            'verification_code': verification_code,
            'verification_url': verification_url,
            'expiry_hours': SVG_VERIFICATION_CONFIG['verification_code_expiry_hours']
        }
        return self.send_email(email, 'account_verification', context=context)
    
    def send_svg_verification_email(self, email: str, username: str, verification_code: str, 
                                  svg_count_today: int, new_svg_filename: str, 
                                  total_svg_count: int, weekly_svg_count: int, monthly_svg_count: int) -> bool:
        """Gửi email xác thực khi lưu file SVG"""
        verification_url = f"{os.environ.get('APP_URL', 'https://yourdomain.com')}/verify-svg?code={verification_code}"
        context = {
            'username': username,
            'email': email,
            'verification_code': verification_code,
            'verification_url': verification_url,
            'svg_count_today': svg_count_today,
            'daily_limit': SVG_VERIFICATION_CONFIG['daily_svg_limit'],
            'new_svg_filename': new_svg_filename,
            'total_svg_count': total_svg_count,
            'weekly_svg_count': weekly_svg_count,
            'monthly_svg_count': monthly_svg_count,
            'expiry_hours': SVG_VERIFICATION_CONFIG['verification_code_expiry_hours']
        }
        return self.send_email(email, 'svg_verification', context=context)
    
    def send_svg_shared_email(self, recipient_email: str, sender_name: str, svg_filename: str, svg_url: str) -> bool:
        """Gửi email thông báo SVG được chia sẻ"""
        context = {
            'sender_name': sender_name,
            'svg_filename': svg_filename,
            'svg_url': svg_url,
            'app_url': os.environ.get('APP_URL', 'https://yourdomain.com')
        }
        return self.send_email(recipient_email, 'svg_shared', context=context)
    
    def send_notification_email(self, recipient_email: str, title: str, message: str, action_url: str = None) -> bool:
        """Gửi email thông báo tùy chỉnh"""
        context = {
            'title': title,
            'message': message,
            'action_url': action_url,
            'app_url': os.environ.get('APP_URL', 'https://yourdomain.com')
        }
        return self.send_email(recipient_email, 'notification', context=context)
    
    def send_profile_settings_verification_email(self, email: str, username: str, verification_code: str, 
                                               changes_summary: List[str] = None, user_id: int = None) -> bool:
        """Gửi email xác thực thay đổi profile settings"""
        base_url = os.environ.get('APP_URL', 'https://yourdomain.com')
        if user_id is not None:
            verification_url = f"{base_url}/profile/{user_id}/settings"
        else:
            verification_url = f"{base_url}/profile/settings"
        context = {
            'username': username,
            'email': email,
            'verification_code': verification_code,
            'verification_url': verification_url,
            'changes_summary': changes_summary or [],
            'expiry_hours': 24,  # Mã có hiệu lực trong 24 giờ
            'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        return self.send_email(email, 'profile_settings_verification', context=context)
    
    def send_admin_notification(self, subject: str, message: str, error_details: str = None) -> bool:
        """Gửi thông báo cho admin"""
        context = {
            'subject': subject,
            'message': message,
            'error_details': error_details,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        success_count = 0
        for admin_email in ADMIN_EMAILS:
            if self.send_email(admin_email, 'notification', subject=subject, context=context):
                success_count += 1
        
        return success_count > 0
    
    def send_bulk_email(self, recipients: List[str], template_name: str, context: Dict = None, delay_seconds: int = 1) -> Dict:
        """
        Gửi email hàng loạt với delay để tránh rate limiting
        
        Returns:
            Dict với thống kê kết quả
        """
        results = {
            'total': len(recipients),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for recipient in recipients:
            try:
                if self.send_email(recipient, template_name, context=context):
                    results['success'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to send to {recipient}")
                
                # Delay giữa các email
                time.sleep(delay_seconds)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(f"Error sending to {recipient}: {str(e)}")
        
        return results
    
    def get_email_stats(self) -> Dict:
        """Lấy thống kê email đã gửi"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor(dictionary=True)
            
            # Thống kê tổng quan
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_emails,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successful_emails,
                    SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed_emails
                FROM email_log
            """)
            overall_stats = cursor.fetchone()
            
            # Thống kê theo template
            cursor.execute("""
                SELECT 
                    template,
                    COUNT(*) as count,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                FROM email_log
                GROUP BY template
                ORDER BY count DESC
            """)
            template_stats = cursor.fetchall()
            
            # Thống kê theo ngày
            cursor.execute("""
                SELECT 
                    DATE(sent_at) as date,
                    COUNT(*) as count,
                    SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as success_count
                FROM email_log
                WHERE sent_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
                GROUP BY DATE(sent_at)
                ORDER BY date DESC
            """)
            daily_stats = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return {
                'overall': overall_stats,
                'by_template': template_stats,
                'daily': daily_stats,
                'rate_limit': self.rate_limit_data
            }
            
        except Exception as e:
            print(f"Error getting email stats: {e}", flush=True)
            return {}

# Global email service instance
email_service = None

def init_email_service(app: Flask):
    """Khởi tạo email service"""
    global email_service
    email_service = EmailService(app)
    return email_service

def get_email_service() -> EmailService:
    """Lấy instance của email service"""
    return email_service
