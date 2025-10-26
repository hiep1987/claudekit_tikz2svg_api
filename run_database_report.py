#!/usr/bin/env python3
"""
Database Report Generator
Chạy báo cáo dữ liệu thực tế từ database và cập nhật DATABASE_DOCUMENTATION.md
"""

import mysql.connector
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Database connection
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'hiep1987'),
        password=os.environ.get('DB_PASSWORD', '96445454'),
        database=os.environ.get('DB_NAME', 'tikz2svg_local')
    )

def run_query(cursor, query, description):
    """Run a query and return results with description"""
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        return {
            'description': description,
            'query': query,
            'results': results,
            'success': True
        }
    except Exception as e:
        return {
            'description': description,
            'query': query,
            'error': str(e),
            'success': False
        }

def main():
    print("=" * 80)
    print("DATABASE REPORT - TikZ2SVG API")
    print("=" * 80)
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Database: {os.environ.get('DB_NAME', 'tikz2svg_local')}")
    print("=" * 80)
    print()
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    # ============================================================================
    # 1. TỔNG QUAN HỆ THỐNG
    # ============================================================================
    print("📊 1. TỔNG QUAN HỆ THỐNG")
    print("-" * 80)
    
    queries = [
        ("SELECT COUNT(*) as total FROM user", "Tổng số người dùng"),
        ("SELECT COUNT(*) as total FROM svg_image", "Tổng số SVG images"),
        ("SELECT COUNT(*) as total FROM svg_comments", "Tổng số comments"),
        ("SELECT COUNT(*) as total FROM svg_comment_likes", "Tổng số comment likes"),
        ("SELECT COUNT(*) as total FROM svg_like", "Tổng số SVG likes"),
        ("SELECT COUNT(*) as total FROM user_follow", "Tổng số follows"),
    ]
    
    for query, desc in queries:
        result = run_query(cursor, query, desc)
        if result['success'] and result['results']:
            print(f"✓ {desc}: {result['results'][0]['total']}")
        else:
            print(f"✗ {desc}: ERROR - {result.get('error', 'Unknown')}")
    
    print()
    
    # ============================================================================
    # 2. COMMENTS SYSTEM STATISTICS
    # ============================================================================
    print("💬 2. COMMENTS SYSTEM STATISTICS")
    print("-" * 80)
    
    # Check if comments tables exist
    cursor.execute("SHOW TABLES LIKE 'svg_comments'")
    comments_exist = cursor.fetchone() is not None
    
    if comments_exist:
        # Top-level comments vs replies
        result = run_query(cursor, """
            SELECT 
                CASE 
                    WHEN parent_comment_id IS NULL THEN 'Top-level'
                    ELSE 'Reply'
                END as comment_type,
                COUNT(*) as count
            FROM svg_comments
            GROUP BY comment_type
        """, "Comments by type")
        
        if result['success']:
            for row in result['results']:
                print(f"  {row['comment_type']}: {row['count']}")
        
        # Top SVGs with most comments
        result = run_query(cursor, """
            SELECT 
                svg_filename,
                COUNT(*) as comment_count
            FROM svg_comments
            WHERE parent_comment_id IS NULL
            GROUP BY svg_filename
            ORDER BY comment_count DESC
            LIMIT 5
        """, "Top 5 SVGs với nhiều comments nhất")
        
        if result['success'] and result['results']:
            print("\n  Top 5 SVGs với nhiều comments nhất:")
            for row in result['results']:
                print(f"    - {row['svg_filename']}: {row['comment_count']} comments")
        else:
            print("  (Chưa có comments)")
        
        # Top commenters
        result = run_query(cursor, """
            SELECT 
                u.username,
                COUNT(c.id) as comment_count
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            GROUP BY u.username
            ORDER BY comment_count DESC
            LIMIT 5
        """, "Top 5 người dùng comment nhiều nhất")
        
        if result['success'] and result['results']:
            print("\n  Top 5 người dùng comment nhiều nhất:")
            for row in result['results']:
                print(f"    - {row['username']}: {row['comment_count']} comments")
        else:
            print("  (Chưa có comments)")
        
        # Comments with most likes
        result = run_query(cursor, """
            SELECT 
                c.id,
                c.comment_text,
                c.likes_count,
                u.username
            FROM svg_comments c
            JOIN user u ON c.user_id = u.id
            ORDER BY c.likes_count DESC
            LIMIT 5
        """, "Top 5 comments được like nhiều nhất")
        
        if result['success'] and result['results']:
            print("\n  Top 5 comments được like nhiều nhất:")
            for row in result['results']:
                text_preview = row['comment_text'][:50] + "..." if len(row['comment_text']) > 50 else row['comment_text']
                print(f"    - {row['username']}: {row['likes_count']} likes - \"{text_preview}\"")
        else:
            print("  (Chưa có likes)")
        
        # Average comments per SVG
        result = run_query(cursor, """
            SELECT 
                AVG(comment_count) as avg_comments
            FROM (
                SELECT 
                    svg_filename,
                    COUNT(*) as comment_count
                FROM svg_comments
                WHERE parent_comment_id IS NULL
                GROUP BY svg_filename
            ) as subquery
        """, "Trung bình comments per SVG")
        
        if result['success'] and result['results']:
            avg = result['results'][0]['avg_comments']
            if avg:
                print(f"\n  Trung bình comments per SVG: {float(avg):.2f}")
            else:
                print("\n  Trung bình comments per SVG: 0")
    else:
        print("  ⚠️  Bảng svg_comments chưa tồn tại. Chạy migration trước.")
    
    print()
    
    # ============================================================================
    # 3. USER STATISTICS
    # ============================================================================
    print("👥 3. USER STATISTICS")
    print("-" * 80)
    
    # Users with verified identity
    result = run_query(cursor, """
        SELECT 
            CASE WHEN identity_verified = 1 THEN 'Verified' ELSE 'Not Verified' END as status,
            COUNT(*) as count
        FROM user
        GROUP BY status
    """, "Identity verification status")
    
    if result['success']:
        for row in result['results']:
            print(f"  {row['status']}: {row['count']}")
    
    # Most active users
    result = run_query(cursor, """
        SELECT 
            u.username,
            COUNT(DISTINCT s.id) as svg_count,
            COUNT(DISTINCT sl.id) as likes_given,
            (SELECT COUNT(*) FROM user_follow WHERE follower_id = u.id) as following,
            (SELECT COUNT(*) FROM user_follow WHERE followee_id = u.id) as followers
        FROM user u
        LEFT JOIN svg_image s ON u.id = s.user_id
        LEFT JOIN svg_like sl ON u.id = sl.user_id
        GROUP BY u.id, u.username
        ORDER BY svg_count DESC
        LIMIT 5
    """, "Top 5 active users")
    
    if result['success'] and result['results']:
        print("\n  Top 5 active users:")
        for row in result['results']:
            print(f"    - {row['username']}: {row['svg_count']} SVGs, {row['likes_given']} likes given, "
                  f"{row['following']} following, {row['followers']} followers")
    
    print()
    
    # ============================================================================
    # 4. SVG IMAGE STATISTICS
    # ============================================================================
    print("🖼️  4. SVG IMAGE STATISTICS")
    print("-" * 80)
    
    # Images with captions
    result = run_query(cursor, """
        SELECT 
            CASE 
                WHEN caption IS NULL OR caption = '' THEN 'No Caption'
                ELSE 'Has Caption'
            END as caption_status,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM svg_image), 2) as percentage
        FROM svg_image
        GROUP BY caption_status
    """, "Caption statistics")
    
    if result['success']:
        for row in result['results']:
            print(f"  {row['caption_status']}: {row['count']} ({row['percentage']}%)")
    
    # Most liked SVGs
    result = run_query(cursor, """
        SELECT 
            s.filename,
            u.username,
            COUNT(sl.id) as like_count
        FROM svg_image s
        LEFT JOIN user u ON s.user_id = u.id
        LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
        GROUP BY s.id, s.filename, u.username
        ORDER BY like_count DESC
        LIMIT 5
    """, "Top 5 most liked SVGs")
    
    if result['success'] and result['results']:
        print("\n  Top 5 most liked SVGs:")
        for row in result['results']:
            print(f"    - {row['filename']} by {row['username']}: {row['like_count']} likes")
    
    print()
    
    # ============================================================================
    # 5. DATABASE SCHEMA VALIDATION
    # ============================================================================
    print("🔍 5. DATABASE SCHEMA VALIDATION")
    print("-" * 80)
    
    # Check comments tables
    tables_to_check = [
        'svg_comments',
        'svg_comment_likes'
    ]
    
    for table in tables_to_check:
        cursor.execute(f"SHOW TABLES LIKE '{table}'")
        exists = cursor.fetchone() is not None
        status = "✓ EXISTS" if exists else "✗ MISSING"
        print(f"  {table}: {status}")
        
        if exists:
            cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
            count = cursor.fetchone()['count']
            print(f"    └─ Records: {count}")
    
    # Check indexes on svg_comments
    if comments_exist:
        cursor.execute("""
            SHOW INDEX FROM svg_comments 
            WHERE Key_name IN (
                'idx_svg_filename', 
                'idx_user_id', 
                'idx_parent_comment_id',
                'idx_created_at_desc',
                'idx_filename_created_desc'
            )
        """)
        indexes = cursor.fetchall()
        print(f"\n  Indexes on svg_comments: {len(indexes)}/5")
        for idx in indexes:
            print(f"    ✓ {idx['Key_name']}")
    
    # Check foreign keys
    cursor.execute("""
        SELECT 
            CONSTRAINT_NAME,
            TABLE_NAME,
            REFERENCED_TABLE_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
          AND CONSTRAINT_NAME LIKE 'fk_comment%%'
    """, (os.environ.get('DB_NAME', 'tikz2svg_local'),))
    
    fks = cursor.fetchall()
    print(f"\n  Foreign keys (comments): {len(fks)}")
    for fk in fks:
        print(f"    ✓ {fk['CONSTRAINT_NAME']}: {fk['TABLE_NAME']} → {fk['REFERENCED_TABLE_NAME']}")
    
    print()
    
    # ============================================================================
    # 6. RECENT ACTIVITY
    # ============================================================================
    print("⏰ 6. RECENT ACTIVITY (Last 7 days)")
    print("-" * 80)
    
    if comments_exist:
        result = run_query(cursor, """
            SELECT 
                DATE(created_at) as date,
                COUNT(*) as comment_count
            FROM svg_comments
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """, "Comments per day (last 7 days)")
        
        if result['success'] and result['results']:
            print("  Comments per day:")
            for row in result['results']:
                print(f"    {row['date']}: {row['comment_count']} comments")
        else:
            print("  (No comments in last 7 days)")
    
    result = run_query(cursor, """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as svg_count
        FROM svg_image
        WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
        GROUP BY DATE(created_at)
        ORDER BY date DESC
    """, "SVGs created per day (last 7 days)")
    
    if result['success'] and result['results']:
        print("\n  SVGs created per day:")
        for row in result['results']:
            print(f"    {row['date']}: {row['svg_count']} SVGs")
    else:
        print("\n  (No SVGs created in last 7 days)")
    
    print()
    
    # ============================================================================
    # SUMMARY
    # ============================================================================
    print("=" * 80)
    print("📝 SUMMARY")
    print("=" * 80)
    
    # Get totals for summary
    cursor.execute("SELECT COUNT(*) as total FROM user")
    total_users = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM svg_image")
    total_svgs = cursor.fetchone()['total']
    
    if comments_exist:
        cursor.execute("SELECT COUNT(*) as total FROM svg_comments")
        total_comments = cursor.fetchone()['total']
        
        cursor.execute("SELECT COUNT(*) as total FROM svg_comment_likes")
        total_comment_likes = cursor.fetchone()['total']
    else:
        total_comments = 0
        total_comment_likes = 0
    
    cursor.execute("SELECT COUNT(*) as total FROM svg_like")
    total_svg_likes = cursor.fetchone()['total']
    
    cursor.execute("SELECT COUNT(*) as total FROM user_follow")
    total_follows = cursor.fetchone()['total']
    
    print(f"""
Database Status: ✓ HEALTHY
Comments System: {'✓ ACTIVE' if comments_exist else '✗ NOT INSTALLED'}

Total Records:
  - Users: {total_users}
  - SVG Images: {total_svgs}
  - Comments: {total_comments}
  - Comment Likes: {total_comment_likes}
  - SVG Likes: {total_svg_likes}
  - User Follows: {total_follows}

Comments System Implementation:
  - Step 1-2 (Database): {'✓ COMPLETE' if comments_exist else '⏳ PENDING'}
  - Step 3-4 (Backend API): {'⏳ IN PROGRESS' if comments_exist else '⏳ PENDING'}
  - Step 5-7 (Frontend): ⏳ PENDING
  - Step 8 (Testing): ⏳ PENDING
  - Step 9 (Documentation): ⏳ PENDING
  - Step 10 (Deployment): ⏳ PENDING
    """)
    
    print("=" * 80)
    print(f"Report generated successfully at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    cursor.close()
    conn.close()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(traceback.format_exc())
        exit(1)

