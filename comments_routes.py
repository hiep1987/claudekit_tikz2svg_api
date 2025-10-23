"""
COMMENTS SYSTEM - API ROUTES
Version: 1.2.1 Final
Date: 2025-10-22

Production-ready API endpoints for Comments feature:
- GET /api/comments/<filename> - Get all comments for an SVG
- POST /api/comments/<filename> - Create a new comment
- PUT /api/comments/<int:comment_id> - Update a comment (owner only)
- DELETE /api/comments/<int:comment_id> - Delete a comment (owner only)
- POST /api/comments/<int:comment_id>/like - Toggle like on a comment
- GET /api/comments/health - Health check endpoint
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from comments_helpers import (
    get_db_connection,
    api_response,
    handle_db_error,
    monitor_performance,
    get_client_ip,
    generate_content_hash,
    detect_spam,
    sanitize_comment_text,
    logger
)
from mysql.connector import Error as MySQLError
import time

# Create Blueprint
comments_bp = Blueprint('comments', __name__, url_prefix='/api/comments')

# =====================================================
# GET COMMENTS FOR AN SVG
# =====================================================

@comments_bp.route('/<filename>', methods=['GET'])
@handle_db_error
@monitor_performance
def get_comments(filename):
    """
    Get all comments for a specific SVG file.
    
    Query Parameters:
    - page (int): Page number for pagination (default: 1)
    - per_page (int): Comments per page (default: 20, max: 100)
    - sort (str): Sort order ('newest' or 'oldest', default: 'newest')
    
    Returns:
        JSON: {
            success: bool,
            data: {
                comments: [array of comment objects],
                pagination: {
                    current_page, per_page, total_comments, total_pages
                },
                user_likes: [array of comment_ids user has liked] (if logged in)
            }
        }
    """
    # Parse query parameters
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(1, int(request.args.get('per_page', 20))))
    sort_order = request.args.get('sort', 'newest')
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Determine sort direction
    order_by = 'created_at DESC' if sort_order == 'newest' else 'created_at ASC'
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Get total count (including replies for better engagement metrics)
        cursor.execute("""
            SELECT COUNT(*) as total
            FROM svg_comments
            WHERE svg_filename = %s
        """, (filename,))
        total_comments = cursor.fetchone()['total']
        
        # Get paginated comments with user info
        cursor.execute(f"""
            SELECT 
                c.id,
                c.comment_text,
                c.created_at,
                c.updated_at,
                c.likes_count,
                c.parent_comment_id,
                u.id as user_id,
                u.username,
                u.avatar,
                u.identity_verified
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            WHERE c.svg_filename = %s AND c.parent_comment_id IS NULL
            ORDER BY {order_by}
            LIMIT %s OFFSET %s
        """, (filename, per_page, offset))
        
        comments = cursor.fetchall()
        
        # For each comment, get its replies
        for comment in comments:
            cursor.execute("""
                SELECT 
                    c.id,
                    c.comment_text,
                    c.created_at,
                    c.updated_at,
                    c.likes_count,
                    c.parent_comment_id,
                    u.id as user_id,
                    u.username,
                    u.avatar,
                    u.identity_verified
                FROM svg_comments c
                JOIN user u ON c.user_id = u.id
                WHERE c.parent_comment_id = %s
                ORDER BY c.created_at ASC
            """, (comment['id'],))
            comment['replies'] = cursor.fetchall()
            
            # Convert datetime to ISO format
            comment['created_at'] = comment['created_at'].isoformat() if comment['created_at'] else None
            comment['updated_at'] = comment['updated_at'].isoformat() if comment['updated_at'] else None
            
            for reply in comment['replies']:
                reply['created_at'] = reply['created_at'].isoformat() if reply['created_at'] else None
                reply['updated_at'] = reply['updated_at'].isoformat() if reply['updated_at'] else None
        
        # Get user's likes (if logged in)
        user_likes = []
        if current_user.is_authenticated:
            cursor.execute("""
                SELECT comment_id
                FROM svg_comment_likes
                WHERE user_id = %s AND comment_id IN (
                    SELECT id FROM svg_comments WHERE svg_filename = %s
                )
            """, (current_user.id, filename))
            user_likes = [row['comment_id'] for row in cursor.fetchall()]
        
        # Calculate pagination
        total_pages = (total_comments + per_page - 1) // per_page
        
        return api_response(
            success=True,
            data={
                'comments': comments,
                'pagination': {
                    'current_page': page,
                    'per_page': per_page,
                    'total_comments': total_comments,
                    'total_pages': total_pages
                },
                'user_likes': user_likes
            },
            status_code=200
        )
        
    finally:
        cursor.close()
        conn.close()

# =====================================================
# CREATE NEW COMMENT
# =====================================================

@comments_bp.route('/<filename>', methods=['POST'])
@login_required
@handle_db_error
@monitor_performance
def create_comment(filename):
    """
    Create a new comment on an SVG file.
    
    Request Body:
    {
        "comment_text": "Comment text (required, max 5000 chars)",
        "parent_comment_id": null or int (for replies)
    }
    
    Returns:
        JSON: {
            success: bool,
            message: str,
            data: {comment object} (if successful)
        }
    """
    data = request.get_json()
    
    # Validate input
    if not data or 'comment_text' not in data:
        return api_response(
            success=False,
            message='Nội dung bình luận không được để trống',
            status_code=400
        )
    
    comment_text = data['comment_text'].strip()
    parent_comment_id = data.get('parent_comment_id')
    
    # Validate length
    if len(comment_text) == 0:
        return api_response(
            success=False,
            message='Nội dung bình luận không được để trống',
            status_code=400
        )
    
    if len(comment_text) > 5000:
        return api_response(
            success=False,
            message='Bình luận không được dài quá 5000 ký tự',
            status_code=400
        )
    
    # Sanitize input
    comment_text = sanitize_comment_text(comment_text)
    
    # Spam detection
    user_ip = get_client_ip()
    is_spam, spam_score, spam_reasons = detect_spam(comment_text, user_ip, current_user.id)
    
    if is_spam:
        logger.warning(f"🚨 Spam comment blocked - User {current_user.id}, IP {user_ip}, Score: {spam_score}")
        return api_response(
            success=False,
            message='Bình luận của bạn được phát hiện là spam. Vui lòng kiểm tra lại nội dung.',
            status_code=400
        )
    
    # Generate content hash for duplicate detection
    content_hash = generate_content_hash(comment_text, current_user.id)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Check for duplicate comment (within last 1 minute)
        cursor.execute("""
            SELECT id FROM svg_comments
            WHERE content_hash = %s 
              AND user_id = %s 
              AND created_at > DATE_SUB(NOW(), INTERVAL 1 MINUTE)
        """, (content_hash, current_user.id))
        
        if cursor.fetchone():
            return api_response(
                success=False,
                message='Bạn đã gửi bình luận giống hệt này rồi. Vui lòng không spam.',
                status_code=400
            )
        
        # Verify SVG exists
        cursor.execute("SELECT filename FROM svg_image WHERE filename = %s", (filename,))
        if not cursor.fetchone():
            return api_response(
                success=False,
                message='Không tìm thấy ảnh SVG',
                status_code=404
            )
        
        # If it's a reply, verify parent comment exists
        if parent_comment_id:
            cursor.execute("""
                SELECT id FROM svg_comments 
                WHERE id = %s AND svg_filename = %s
            """, (parent_comment_id, filename))
            if not cursor.fetchone():
                return api_response(
                    success=False,
                    message='Không tìm thấy bình luận gốc',
                    status_code=404
                )
        
        # Insert comment
        cursor.execute("""
            INSERT INTO svg_comments 
            (svg_filename, user_id, comment_text, parent_comment_id, user_ip, content_hash)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (filename, current_user.id, comment_text, parent_comment_id, user_ip, content_hash))
        
        comment_id = cursor.lastrowid
        
        # Update comments_count in svg_image (only for top-level comments)
        if not parent_comment_id:
            cursor.execute("""
                UPDATE svg_image 
                SET comments_count = comments_count + 1 
                WHERE filename = %s
            """, (filename,))
        
        conn.commit()
        
        # Fetch the created comment with user info
        cursor.execute("""
            SELECT 
                c.id,
                c.comment_text,
                c.created_at,
                c.updated_at,
                c.likes_count,
                c.parent_comment_id,
                u.id as user_id,
                u.username,
                u.avatar,
                u.identity_verified
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            WHERE c.id = %s
        """, (comment_id,))
        
        comment = cursor.fetchone()
        comment['created_at'] = comment['created_at'].isoformat() if comment['created_at'] else None
        comment['updated_at'] = comment['updated_at'].isoformat() if comment['updated_at'] else None
        comment['replies'] = []
        
        logger.info(f"✅ Comment created: ID {comment_id}, User {current_user.id}, SVG {filename}")
        
        return api_response(
            success=True,
            message='Đã thêm bình luận thành công',
            data={'comment': comment},
            status_code=201
        )
        
    finally:
        cursor.close()
        conn.close()

# =====================================================
# UPDATE COMMENT (OWNER ONLY)
# =====================================================

@comments_bp.route('/<int:comment_id>', methods=['PUT'])
@login_required
@handle_db_error
@monitor_performance
def update_comment(comment_id):
    """
    Update an existing comment (owner only).
    
    Request Body:
    {
        "comment_text": "Updated comment text"
    }
    
    Returns:
        JSON: {success, message, data}
    """
    data = request.get_json()
    
    if not data or 'comment_text' not in data:
        return api_response(
            success=False,
            message='Nội dung bình luận không được để trống',
            status_code=400
        )
    
    comment_text = data['comment_text'].strip()
    
    if len(comment_text) == 0:
        return api_response(
            success=False,
            message='Nội dung bình luận không được để trống',
            status_code=400
        )
    
    if len(comment_text) > 5000:
        return api_response(
            success=False,
            message='Bình luận không được dài quá 5000 ký tự',
            status_code=400
        )
    
    comment_text = sanitize_comment_text(comment_text)
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify ownership
        cursor.execute("""
            SELECT user_id FROM svg_comments WHERE id = %s
        """, (comment_id,))
        
        comment = cursor.fetchone()
        
        if not comment:
            return api_response(
                success=False,
                message='Không tìm thấy bình luận',
                status_code=404
            )
        
        if comment['user_id'] != current_user.id:
            return api_response(
                success=False,
                message='Bạn không có quyền chỉnh sửa bình luận này',
                status_code=403
            )
        
        # Update comment
        cursor.execute("""
            UPDATE svg_comments 
            SET comment_text = %s, updated_at = NOW()
            WHERE id = %s
        """, (comment_text, comment_id))
        
        conn.commit()
        
        logger.info(f"✅ Comment updated: ID {comment_id}, User {current_user.id}")
        
        return api_response(
            success=True,
            message='Đã cập nhật bình luận thành công',
            data={'comment_text': comment_text},
            status_code=200
        )
        
    finally:
        cursor.close()
        conn.close()

# =====================================================
# DELETE COMMENT (OWNER ONLY)
# =====================================================

@comments_bp.route('/<int:comment_id>', methods=['DELETE'])
@login_required
@handle_db_error
@monitor_performance
def delete_comment(comment_id):
    """
    Delete a comment (owner only).
    Cascade deletes replies and likes.
    
    Returns:
        JSON: {success, message}
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify ownership and get SVG filename
        cursor.execute("""
            SELECT user_id, svg_filename, parent_comment_id 
            FROM svg_comments 
            WHERE id = %s
        """, (comment_id,))
        
        comment = cursor.fetchone()
        
        if not comment:
            return api_response(
                success=False,
                message='Không tìm thấy bình luận',
                status_code=404
            )
        
        if comment['user_id'] != current_user.id:
            return api_response(
                success=False,
                message='Bạn không có quyền xóa bình luận này',
                status_code=403
            )
        
        # Delete comment (cascade will handle replies and likes)
        cursor.execute("DELETE FROM svg_comments WHERE id = %s", (comment_id,))
        
        # Update comments_count in svg_image (only for top-level comments)
        if not comment['parent_comment_id']:
            cursor.execute("""
                UPDATE svg_image 
                SET comments_count = GREATEST(comments_count - 1, 0)
                WHERE filename = %s
            """, (comment['svg_filename'],))
        
        conn.commit()
        
        logger.info(f"✅ Comment deleted: ID {comment_id}, User {current_user.id}")
        
        return api_response(
            success=True,
            message='Đã xóa bình luận thành công',
            status_code=200
        )
        
    finally:
        cursor.close()
        conn.close()

# =====================================================
# TOGGLE LIKE ON COMMENT
# =====================================================

@comments_bp.route('/<int:comment_id>/like', methods=['POST'])
@login_required
@handle_db_error
@monitor_performance
def toggle_like(comment_id):
    """
    Toggle like status on a comment.
    
    Returns:
        JSON: {
            success, 
            message, 
            data: {
                liked: bool,
                likes_count: int
            }
        }
    """
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        # Verify comment exists
        cursor.execute("""
            SELECT id, likes_count FROM svg_comments WHERE id = %s
        """, (comment_id,))
        
        comment = cursor.fetchone()
        
        if not comment:
            return api_response(
                success=False,
                message='Không tìm thấy bình luận',
                status_code=404
            )
        
        # Check if already liked
        cursor.execute("""
            SELECT id FROM svg_comment_likes 
            WHERE comment_id = %s AND user_id = %s
        """, (comment_id, current_user.id))
        
        existing_like = cursor.fetchone()
        
        if existing_like:
            # Unlike
            cursor.execute("""
                DELETE FROM svg_comment_likes 
                WHERE comment_id = %s AND user_id = %s
            """, (comment_id, current_user.id))
            
            cursor.execute("""
                UPDATE svg_comments 
                SET likes_count = GREATEST(likes_count - 1, 0)
                WHERE id = %s
            """, (comment_id,))
            
            liked = False
            message = 'Đã bỏ thích bình luận'
        else:
            # Like
            cursor.execute("""
                INSERT INTO svg_comment_likes (comment_id, user_id)
                VALUES (%s, %s)
            """, (comment_id, current_user.id))
            
            cursor.execute("""
                UPDATE svg_comments 
                SET likes_count = likes_count + 1
                WHERE id = %s
            """, (comment_id,))
            
            liked = True
            message = 'Đã thích bình luận'
        
        conn.commit()
        
        # Get updated likes count
        cursor.execute("SELECT likes_count FROM svg_comments WHERE id = %s", (comment_id,))
        likes_count = cursor.fetchone()['likes_count']
        
        logger.info(f"✅ Like toggled: Comment {comment_id}, User {current_user.id}, Liked: {liked}")
        
        return api_response(
            success=True,
            message=message,
            data={
                'liked': liked,
                'likes_count': likes_count
            },
            status_code=200
        )
        
    finally:
        cursor.close()
        conn.close()

# =====================================================
# HEALTH CHECK
# =====================================================

@comments_bp.route('/health', methods=['GET'])
@handle_db_error
def health_check():
    """
    Health check endpoint for monitoring.
    
    Returns:
        JSON: {success, data: {status, database, timestamp}}
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Test database connection
        cursor.execute("SELECT 1")
        cursor.fetchone()
        db_status = 'ok'
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        db_status = 'error'
    finally:
        cursor.close()
        conn.close()
    
    return api_response(
        success=(db_status == 'ok'),
        data={
            'status': 'ok' if db_status == 'ok' else 'degraded',
            'database': db_status,
            'timestamp': int(time.time())
        },
        status_code=200 if db_status == 'ok' else 503
    )

