"""
Notification Service for TikZ to SVG API
Handles in-app notifications for user interactions (likes, comments, follows)
"""

import mysql.connector
from typing import Optional, List, Dict, Tuple
from datetime import datetime
import re
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotificationService:
    """
    Service xử lý notifications với security và performance optimizations
    
    Features:
    - Input validation and sanitization
    - SQL injection protection
    - Efficient database queries with indexes
    - Comprehensive error handling
    - Structured logging
    """
    
    def __init__(self, db_config: Optional[Dict] = None):
        """
        Initialize NotificationService
        
        Args:
            db_config: Database configuration dict with keys:
                      host, user, password, database
                      If None, reads from environment variables
        """
        if db_config is None:
            # Use environment variables (same as app.py pattern)
            self.db_config = {
                'host': os.environ.get('DB_HOST', 'localhost'),
                'user': os.environ.get('DB_USER', 'hiep1987'),
                'password': os.environ.get('DB_PASSWORD', ''),
                'database': os.environ.get('DB_NAME', 'tikz2svg')
            }
        else:
            self.db_config = db_config
        
        self._validate_db_config()
        logger.info("✅ NotificationService initialized successfully")
    
    def _validate_db_config(self):
        """Validate database configuration"""
        required_keys = ['host', 'user', 'password', 'database']
        for key in required_keys:
            if key not in self.db_config:
                raise ValueError(f"Missing database config: {key}")
    
    def _get_connection(self):
        """Get database connection"""
        return mysql.connector.connect(**self.db_config)
    
    def _validate_target_id(self, target_type: str, target_id: str) -> bool:
        """
        Validate target ID format để tránh injection
        
        Args:
            target_type: 'svg_image', 'comment', or 'user'
            target_id: ID to validate
        
        Returns:
            True if valid, False otherwise
        """
        if target_type == 'svg_image':
            # Chỉ cho phép alphanumeric, underscore, hyphen, và .svg extension
            pattern = r'^[a-zA-Z0-9_\-]+\.svg$'
            return bool(re.match(pattern, target_id))
        elif target_type in ['comment', 'user']:
            # Chỉ cho phép số
            return target_id.isdigit()
        return False
    
    def _sanitize_content(self, content: Optional[str]) -> Optional[str]:
        """
        Sanitize notification content
        
        Args:
            content: Raw content string
        
        Returns:
            Sanitized content (max 200 chars, no HTML)
        """
        if not content:
            return None
        
        # Strip HTML tags
        content = re.sub(r'<[^>]+>', '', content)
        
        # Remove multiple whitespaces
        content = re.sub(r'\s+', ' ', content)
        
        # Trim and limit to 200 characters
        content = content.strip()[:200]
        
        return content if content else None
    
    def create_notification(
        self,
        user_id: int,
        actor_id: int,
        notification_type: str,
        target_type: str,
        target_id: str,
        content: Optional[str] = None,
        action_url: Optional[str] = None
    ) -> int:
        """
        Tạo notification mới với validation và error handling
        
        Args:
            user_id: ID người nhận notification
            actor_id: ID người thực hiện hành động
            notification_type: 'comment', 'like', 'reply', 'follow'
            target_type: 'svg_image', 'comment', 'user'
            target_id: ID của target object
            content: Optional preview content (will be sanitized)
            action_url: Optional URL to navigate to
        
        Returns:
            notification_id if successful, 0 if failed or skipped
        """
        try:
            # Validation 1: Không tạo notification cho self-interaction
            if user_id == actor_id:
                logger.info(f"Skipping self-notification: user_id={user_id}")
                return 0
            
            # Validation 2: Validate target_id format
            if not self._validate_target_id(target_type, target_id):
                logger.warning(f"Invalid target_id: {target_type}={target_id}")
                return 0
            
            # Validation 3: Validate notification_type
            valid_types = ['comment', 'comment_social', 'like', 'reply', 'follow']
            if notification_type not in valid_types:
                logger.warning(f"Invalid notification_type: {notification_type}")
                return 0
            
            # Validation 4: Validate target_type
            valid_targets = ['svg_image', 'comment', 'user']
            if target_type not in valid_targets:
                logger.warning(f"Invalid target_type: {target_type}")
                return 0
            
            # Sanitize content
            content = self._sanitize_content(content)
            
            # Validate action_url (must be internal path)
            if action_url and not action_url.startswith('/'):
                logger.warning(f"Invalid action_url (must start with /): {action_url}")
                action_url = None
            
            # Database operation
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    INSERT INTO notifications
                    (user_id, actor_id, notification_type, target_type, target_id, content, action_url)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, actor_id, notification_type, target_type, target_id, content, action_url))
                
                conn.commit()
                notif_id = cursor.lastrowid
                
                logger.info(
                    f"✅ Created notification {notif_id}: "
                    f"{notification_type} from user_{actor_id} to user_{user_id} "
                    f"(target: {target_type}:{target_id})"
                )
                
                return notif_id
            
            except mysql.connector.Error as e:
                conn.rollback()
                logger.error(f"❌ Database error creating notification: {e}")
                return 0
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error creating notification: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def get_user_notifications(
        self,
        user_id: int,
        limit: int = 20,
        only_unread: bool = False
    ) -> List[Dict]:
        """
        Lấy danh sách notifications của user
        
        Args:
            user_id: ID của user
            limit: Số lượng notifications tối đa (default 20)
            only_unread: Chỉ lấy unread notifications (default False)
        
        Returns:
            List of notification dictionaries with actor info
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            try:
                query = """
                    SELECT 
                        n.*,
                        u.username as actor_username,
                        u.avatar as actor_avatar
                    FROM notifications n
                    JOIN user u ON n.actor_id = u.id
                    WHERE n.user_id = %s
                """
                
                params = [user_id]
                
                if only_unread:
                    query += " AND n.is_read = FALSE"
                
                query += " ORDER BY n.created_at DESC LIMIT %s"
                params.append(limit)
                
                cursor.execute(query, params)
                notifications = cursor.fetchall()
                
                logger.info(
                    f"📋 Retrieved {len(notifications)} notifications for user_{user_id} "
                    f"(only_unread={only_unread})"
                )
                
                return notifications
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error getting notifications for user_{user_id}: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_unread_count(self, user_id: int) -> int:
        """
        Đếm số notifications chưa đọc của user
        
        Args:
            user_id: ID của user
        
        Returns:
            Number of unread notifications
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Sử dụng composite index idx_user_unread để optimize query
                cursor.execute("""
                    SELECT COUNT(*) FROM notifications
                    WHERE user_id = %s AND is_read = FALSE
                """, (user_id,))
                
                result = cursor.fetchone()
                count = result[0] if result else 0
                
                logger.debug(f"🔔 User_{user_id} has {count} unread notifications")
                
                return count
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error counting unread notifications for user_{user_id}: {e}")
            return 0
    
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """
        Đánh dấu notification đã đọc
        
        Args:
            notification_id: ID của notification
            user_id: ID của user (for security check)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                # Security: Chỉ cho phép user owner mark as read
                cursor.execute("""
                    UPDATE notifications
                    SET is_read = TRUE, read_at = NOW()
                    WHERE id = %s AND user_id = %s AND is_read = FALSE
                """, (notification_id, user_id))
                
                conn.commit()
                
                if cursor.rowcount > 0:
                    logger.info(f"✅ Marked notification_{notification_id} as read for user_{user_id}")
                    return True
                else:
                    logger.warning(
                        f"⚠️ Failed to mark notification_{notification_id} as read "
                        f"(not found or already read or wrong user)"
                    )
                    return False
            
            except mysql.connector.Error as e:
                conn.rollback()
                logger.error(f"❌ Database error marking notification as read: {e}")
                return False
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error marking notification_{notification_id} as read: {e}")
            return False
    
    def mark_all_as_read(self, user_id: int) -> int:
        """
        Đánh dấu tất cả notifications của user đã đọc
        
        Args:
            user_id: ID của user
        
        Returns:
            Number of notifications marked as read
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                cursor.execute("""
                    UPDATE notifications
                    SET is_read = TRUE, read_at = NOW()
                    WHERE user_id = %s AND is_read = FALSE
                """, (user_id,))
                
                conn.commit()
                count = cursor.rowcount
                
                logger.info(f"✅ Marked {count} notifications as read for user_{user_id}")
                
                return count
            
            except mysql.connector.Error as e:
                conn.rollback()
                logger.error(f"❌ Database error marking all as read: {e}")
                return 0
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error marking all notifications as read for user_{user_id}: {e}")
            return 0
    
    def delete_old_notifications(self, days: int = 90, only_read: bool = True) -> int:
        """
        Xóa notifications cũ (maintenance task)
        
        Args:
            days: Số ngày (notifications cũ hơn sẽ bị xóa)
            only_read: Chỉ xóa notifications đã đọc (default True)
        
        Returns:
            Number of notifications deleted
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            try:
                query = """
                    DELETE FROM notifications
                    WHERE created_at < DATE_SUB(NOW(), INTERVAL %s DAY)
                """
                
                if only_read:
                    query += " AND is_read = TRUE"
                
                cursor.execute(query, (days,))
                conn.commit()
                count = cursor.rowcount
                
                logger.info(
                    f"🗑️ Deleted {count} notifications older than {days} days "
                    f"(only_read={only_read})"
                )
                
                return count
            
            except mysql.connector.Error as e:
                conn.rollback()
                logger.error(f"❌ Database error deleting old notifications: {e}")
                return 0
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error deleting old notifications: {e}")
            return 0
    
    def get_notification_stats(self, user_id: Optional[int] = None) -> Dict:
        """
        Lấy thống kê notifications (for analytics/debugging)
        
        Args:
            user_id: Optional user_id to filter stats
        
        Returns:
            Dictionary with notification statistics
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor(dictionary=True)
            
            try:
                if user_id:
                    # Stats for specific user
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread,
                            SUM(CASE WHEN is_read = TRUE THEN 1 ELSE 0 END) as read,
                            COUNT(DISTINCT notification_type) as types_count,
                            MAX(created_at) as latest_notification
                        FROM notifications
                        WHERE user_id = %s
                    """, (user_id,))
                else:
                    # Global stats
                    cursor.execute("""
                        SELECT 
                            COUNT(*) as total,
                            SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread,
                            SUM(CASE WHEN is_read = TRUE THEN 1 ELSE 0 END) as read,
                            COUNT(DISTINCT user_id) as unique_recipients,
                            COUNT(DISTINCT actor_id) as unique_actors
                        FROM notifications
                    """)
                
                stats = cursor.fetchone()
                
                logger.info(f"📊 Notification stats retrieved for user_{user_id if user_id else 'all'}")
                
                return stats if stats else {}
            
            finally:
                cursor.close()
                conn.close()
        
        except Exception as e:
            logger.error(f"❌ Error getting notification stats: {e}")
            return {}


# Singleton instance (optional - can be initialized per request)
_notification_service_instance = None


def get_notification_service() -> NotificationService:
    """
    Get singleton instance of NotificationService
    
    Returns:
        NotificationService instance
    """
    global _notification_service_instance
    
    if _notification_service_instance is None:
        _notification_service_instance = NotificationService()
    
    return _notification_service_instance


# For backwards compatibility and convenience
def init_notification_service(db_config: Optional[Dict] = None) -> NotificationService:
    """
    Initialize notification service with custom config
    
    Args:
        db_config: Optional database configuration
    
    Returns:
        NotificationService instance
    """
    global _notification_service_instance
    _notification_service_instance = NotificationService(db_config)
    return _notification_service_instance

