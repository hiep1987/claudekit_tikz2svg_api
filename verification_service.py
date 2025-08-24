"""
Verification Service cho TikZ2SVG API
Quản lý mã xác thực và kiểm tra giới hạn SVG
"""

import os
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import mysql.connector
from dotenv import load_dotenv
from email_service import get_email_service

load_dotenv()

class VerificationService:
    def __init__(self):
        self.email_service = get_email_service()
    
    def generate_verification_code(self, length: int = 6) -> str:
        """Tạo mã xác thực ngẫu nhiên"""
        return ''.join(secrets.choice(string.digits) for _ in range(length))
    
    def create_verification_token(self, user_id: int, verification_type: str, 
                                expires_in_hours: int = 24) -> str:
        """Tạo token xác thực và lưu vào database"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=expires_in_hours)
        
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor()
            
            # Xóa token cũ nếu có
            cursor.execute("""
                DELETE FROM verification_tokens 
                WHERE user_id = %s AND verification_type = %s
            """, (user_id, verification_type))
            
            # Thêm token mới
            cursor.execute("""
                INSERT INTO verification_tokens (user_id, token, verification_type, expires_at)
                VALUES (%s, %s, %s, %s)
            """, (user_id, token, verification_type, expires_at))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return token
            
        except Exception as e:
            print(f"Error creating verification token: {e}", flush=True)
            return None
    
    def verify_token(self, token: str, verification_type: str) -> Optional[int]:
        """Xác thực token và trả về user_id nếu hợp lệ"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT user_id, expires_at, used
                FROM verification_tokens 
                WHERE token = %s AND verification_type = %s
            """, (token, verification_type))
            
            row = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if not row:
                return None
            
            # Kiểm tra token đã hết hạn chưa
            if datetime.now() > row['expires_at']:
                return None
            
            # Kiểm tra token đã được sử dụng chưa
            if row['used']:
                return None
            
            return row['user_id']
            
        except Exception as e:
            print(f"Error verifying token: {e}", flush=True)
            return None
    
    def mark_token_as_used(self, token: str) -> bool:
        """Đánh dấu token đã được sử dụng"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE verification_tokens 
                SET used = TRUE, used_at = %s
                WHERE token = %s
            """, (datetime.now(), token))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error marking token as used: {e}", flush=True)
            return False
    
    def get_user_svg_stats(self, user_id: int) -> Dict:
        """Lấy thống kê SVG của user"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor(dictionary=True)
            
            # SVG hôm nay
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM svg_image 
                WHERE user_id = %s AND DATE(created_at) = CURDATE()
            """, (user_id,))
            today_count = cursor.fetchone()['count']
            
            # SVG tuần này
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM svg_image 
                WHERE user_id = %s AND YEARWEEK(created_at) = YEARWEEK(NOW())
            """, (user_id,))
            weekly_count = cursor.fetchone()['count']
            
            # SVG tháng này
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM svg_image 
                WHERE user_id = %s AND YEAR(created_at) = YEAR(NOW()) AND MONTH(created_at) = MONTH(NOW())
            """, (user_id,))
            monthly_count = cursor.fetchone()['count']
            
            # Tổng SVG
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM svg_image 
                WHERE user_id = %s
            """, (user_id,))
            total_count = cursor.fetchone()['count']
            
            cursor.close()
            conn.close()
            
            return {
                'today': today_count,
                'weekly': weekly_count,
                'monthly': monthly_count,
                'total': total_count
            }
            
        except Exception as e:
            print(f"Error getting user SVG stats: {e}", flush=True)
            return {'today': 0, 'weekly': 0, 'monthly': 0, 'total': 0}
    
    def check_svg_verification_required(self, user_id: int) -> Tuple[bool, Dict]:
        """Kiểm tra xem có cần xác thực khi lưu SVG không"""
        stats = self.get_user_svg_stats(user_id)
        daily_limit = int(os.environ.get('DAILY_SVG_LIMIT', 10))
        
        requires_verification = stats['today'] >= daily_limit
        
        return requires_verification, stats
    
    def send_account_verification(self, user_id: int, email: str, username: str) -> bool:
        """Gửi email xác thực tài khoản"""
        if not self.email_service:
            print("Email service not available", flush=True)
            return False
        
        verification_code = self.generate_verification_code()
        
        # Lưu mã xác thực vào database
        token = self.create_verification_token(user_id, 'account_verification')
        if not token:
            return False
        
        # Gửi email
        success = self.email_service.send_account_verification_email(
            email=email,
            username=username,
            verification_code=verification_code
        )
        
        if success:
            # Lưu mã xác thực vào database
            try:
                conn = mysql.connector.connect(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    user=os.environ.get('DB_USER', 'hiep1987'),
                    password=os.environ.get('DB_PASSWORD', ''),
                    database=os.environ.get('DB_NAME', 'tikz2svg')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE verification_tokens 
                    SET verification_code = %s
                    WHERE token = %s
                """, (verification_code, token))
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error saving verification code: {e}", flush=True)
        
        return success
    
    def send_svg_verification(self, user_id: int, email: str, username: str, 
                            new_svg_filename: str) -> bool:
        """Gửi email xác thực khi lưu SVG"""
        if not self.email_service:
            print("Email service not available", flush=True)
            return False
        
        # Lấy thống kê SVG
        stats = self.get_user_svg_stats(user_id)
        
        verification_code = self.generate_verification_code()
        
        # Lưu token xác thực
        token = self.create_verification_token(user_id, 'svg_verification')
        if not token:
            return False
        
        # Gửi email
        success = self.email_service.send_svg_verification_email(
            email=email,
            username=username,
            verification_code=verification_code,
            svg_count_today=stats['today'],
            new_svg_filename=new_svg_filename,
            total_svg_count=stats['total'],
            weekly_svg_count=stats['weekly'],
            monthly_svg_count=stats['monthly']
        )
        
        if success:
            # Lưu mã xác thực vào database
            try:
                conn = mysql.connector.connect(
                    host=os.environ.get('DB_HOST', 'localhost'),
                    user=os.environ.get('DB_USER', 'hiep1987'),
                    password=os.environ.get('DB_PASSWORD', ''),
                    database=os.environ.get('DB_NAME', 'tikz2svg')
                )
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE verification_tokens 
                    SET verification_code = %s
                    WHERE token = %s
                """, (verification_code, token))
                
                conn.commit()
                cursor.close()
                conn.close()
                
            except Exception as e:
                print(f"Error saving verification code: {e}", flush=True)
        
        return success
    
    def verify_account(self, verification_code: str) -> bool:
        """Xác thực tài khoản bằng mã"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor(dictionary=True)
            
            # Tìm token với mã xác thực
            cursor.execute("""
                SELECT vt.user_id, vt.token, vt.expires_at, vt.used
                FROM verification_tokens vt
                WHERE vt.verification_code = %s AND vt.verification_type = 'account_verification'
            """, (verification_code,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            # Kiểm tra token đã hết hạn chưa
            if datetime.now() > row['expires_at']:
                return False
            
            # Kiểm tra token đã được sử dụng chưa
            if row['used']:
                return False
            
            # Cập nhật trạng thái xác thực user
            cursor.execute("""
                UPDATE user 
                SET email_verified = TRUE, email_verification_token = NULL
                WHERE id = %s
            """, (row['user_id'],))
            
            # Đánh dấu token đã sử dụng
            cursor.execute("""
                UPDATE verification_tokens 
                SET used = TRUE, used_at = %s
                WHERE token = %s
            """, (datetime.now(), row['token']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error verifying account: {e}", flush=True)
            return False
    
    def verify_svg_save(self, verification_code: str) -> bool:
        """Xác thực lưu SVG bằng mã"""
        try:
            conn = mysql.connector.connect(
                host=os.environ.get('DB_HOST', 'localhost'),
                user=os.environ.get('DB_USER', 'hiep1987'),
                password=os.environ.get('DB_PASSWORD', ''),
                database=os.environ.get('DB_NAME', 'tikz2svg')
            )
            cursor = conn.cursor(dictionary=True)
            
            # Tìm token với mã xác thực
            cursor.execute("""
                SELECT vt.user_id, vt.token, vt.expires_at, vt.used
                FROM verification_tokens vt
                WHERE vt.verification_code = %s AND vt.verification_type = 'svg_verification'
            """, (verification_code,))
            
            row = cursor.fetchone()
            if not row:
                return False
            
            # Kiểm tra token đã hết hạn chưa
            if datetime.now() > row['expires_at']:
                return False
            
            # Kiểm tra token đã được sử dụng chưa
            if row['used']:
                return False
            
            # Đánh dấu token đã sử dụng
            cursor.execute("""
                UPDATE verification_tokens 
                SET used = TRUE, used_at = %s
                WHERE token = %s
            """, (datetime.now(), row['token']))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"Error verifying SVG save: {e}", flush=True)
            return False

# Global verification service instance
verification_service = None

def init_verification_service():
    """Khởi tạo verification service"""
    global verification_service
    verification_service = VerificationService()
    return verification_service

def get_verification_service() -> VerificationService:
    """Lấy instance của verification service"""
    return verification_service
