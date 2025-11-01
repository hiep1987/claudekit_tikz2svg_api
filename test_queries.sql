-- =====================================================
-- PHASE 1 & 2 SQL QUERIES VERIFICATION TEST
-- =====================================================

USE tikz2svg_local;

-- Test 1: Count total items
SELECT 'Test 1: Count Total Items' as test_name;
SELECT COUNT(*) as total FROM svg_image;

-- Test 2: Verify svg_image columns exist
SELECT 'Test 2: Verify svg_image columns' as test_name;
DESCRIBE svg_image;

-- Test 3: Verify svg_comments columns exist
SELECT 'Test 3: Verify svg_comments columns' as test_name;
DESCRIBE svg_comments;

-- Test 4: Verify svg_like columns exist
SELECT 'Test 4: Verify svg_like columns' as test_name;
DESCRIBE svg_like;

-- Test 5: Test pagination query (first 5 rows)
SELECT 'Test 5: Pagination Query (LIMIT 5)' as test_name;
SELECT 
    s.id,
    s.filename,
    s.created_at,
    s.user_id,
    s.tikz_code,
    s.keywords,
    u.id as creator_id,
    COALESCE(u.username, 'Anonymous') as creator_username,
    COUNT(DISTINCT c.id) as comment_count,
    COUNT(DISTINCT sl.id) as like_count,
    CASE WHEN user_like.id IS NOT NULL THEN 1 ELSE 0 END as is_liked_by_current_user
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN svg_comments c ON s.filename = c.svg_filename
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
LEFT JOIN svg_like user_like ON s.id = user_like.svg_image_id AND user_like.user_id = 0
GROUP BY s.id, s.filename, s.created_at, s.user_id, s.tikz_code, s.keywords, u.id, u.username, user_like.id
ORDER BY s.created_at DESC
LIMIT 5 OFFSET 0;

-- Test 6: Check if JOINs are working correctly
SELECT 'Test 6: Join Statistics' as test_name;
SELECT 
    'svg_image' as table_name,
    COUNT(*) as total_rows
FROM svg_image
UNION ALL
SELECT 
    'user' as table_name,
    COUNT(*) as total_rows
FROM user
UNION ALL
SELECT 
    'svg_comments' as table_name,
    COUNT(*) as total_rows
FROM svg_comments
UNION ALL
SELECT 
    'svg_like' as table_name,
    COUNT(*) as total_rows
FROM svg_like;

-- Test 7: Verify JOIN keys exist
SELECT 'Test 7: Verify JOIN relationships' as test_name;
SELECT 
    'svg_image -> user' as relationship,
    COUNT(DISTINCT s.user_id) as svg_with_user,
    COUNT(DISTINCT u.id) as matched_users
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
UNION ALL
SELECT 
    'svg_image -> svg_comments' as relationship,
    COUNT(DISTINCT s.filename) as svg_with_comments,
    COUNT(DISTINCT c.svg_filename) as matched_comments
FROM svg_image s
LEFT JOIN svg_comments c ON s.filename = c.svg_filename
UNION ALL
SELECT 
    'svg_image -> svg_like' as relationship,
    COUNT(DISTINCT s.id) as svg_with_likes,
    COUNT(DISTINCT sl.svg_image_id) as matched_likes
FROM svg_image s
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id;

-- Test 8: Test with real user_id (if exists)
SELECT 'Test 8: Test with real user_id' as test_name;
SELECT 
    s.id,
    s.filename,
    COALESCE(u.username, 'Anonymous') as creator,
    COUNT(DISTINCT c.id) as comments,
    COUNT(DISTINCT sl.id) as likes
FROM svg_image s
LEFT JOIN user u ON s.user_id = u.id
LEFT JOIN svg_comments c ON s.filename = c.svg_filename
LEFT JOIN svg_like sl ON s.id = sl.svg_image_id
GROUP BY s.id, s.filename, u.username
ORDER BY s.created_at DESC
LIMIT 10;

