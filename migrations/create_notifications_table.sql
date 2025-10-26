-- ================================================================
-- Notifications System - Database Migration
-- ================================================================
-- Purpose: Create notifications table for in-app notifications
-- Author: AI Assistant
-- Date: 2025-10-24
-- Database: tikz2svg (MySQL 8.0+)
-- ================================================================

-- Create notifications table
CREATE TABLE IF NOT EXISTS `notifications` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT 'Unique notification ID',
  `user_id` INT NOT NULL COMMENT 'User receiving the notification (notification owner)',
  `actor_id` INT NOT NULL COMMENT 'User who performed the action (actor)',
  `notification_type` ENUM('comment', 'like', 'reply', 'follow') NOT NULL COMMENT 'Type of notification',
  `target_type` ENUM('svg_image', 'comment', 'user') NOT NULL COMMENT 'Type of target object',
  `target_id` VARCHAR(255) NOT NULL COMMENT 'ID of target (svg_filename, comment_id, or user_id)',
  `content` TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'Optional content preview (max 200 chars)',
  `action_url` VARCHAR(500) DEFAULT NULL COMMENT 'URL to navigate when notification is clicked',
  `is_read` BOOLEAN DEFAULT FALSE COMMENT 'Whether notification has been read',
  `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT 'When notification was created',
  `read_at` TIMESTAMP NULL DEFAULT NULL COMMENT 'When notification was marked as read',
  
  -- Foreign Keys for referential integrity
  FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  FOREIGN KEY (`actor_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  
  -- Indexes for query optimization
  INDEX `idx_user_id` (`user_id`) COMMENT 'Fast lookup by recipient user',
  INDEX `idx_is_read` (`is_read`) COMMENT 'Filter by read status',
  INDEX `idx_created_at` (`created_at`) COMMENT 'Sort by creation time',
  INDEX `idx_user_unread` (`user_id`, `is_read`, `created_at`) COMMENT 'Composite index for unread notifications query',
  INDEX `idx_actor_type` (`actor_id`, `notification_type`, `created_at`) COMMENT 'Analytics queries by actor',
  
  -- Data validation constraint
  CONSTRAINT `chk_target_type_id` CHECK (
    (target_type = 'svg_image' AND target_id REGEXP '^[a-zA-Z0-9_\\-]+\\.svg$') OR
    (target_type = 'comment' AND target_id REGEXP '^[0-9]+$') OR
    (target_type = 'user' AND target_id REGEXP '^[0-9]+$')
  )
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Stores in-app notifications for user interactions (likes, comments, follows)';

-- ================================================================
-- Verification Queries
-- ================================================================

-- Check if table was created successfully
SELECT 
    TABLE_NAME,
    ENGINE,
    TABLE_ROWS,
    DATA_LENGTH,
    INDEX_LENGTH,
    CREATE_TIME
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
AND TABLE_NAME = 'notifications';

-- Show table structure
DESCRIBE notifications;

-- Show all indexes
SHOW INDEXES FROM notifications;

-- ================================================================
-- Sample Data for Testing (Optional - Comment out for production)
-- ================================================================

-- Uncomment below to insert sample notifications for testing

/*
-- Sample notification: User 2 liked User 1's SVG
INSERT INTO notifications (user_id, actor_id, notification_type, target_type, target_id, action_url)
VALUES (1, 2, 'like', 'svg_image', 'example_1234567890.svg', '/view_svg/example_1234567890.svg');

-- Sample notification: User 3 commented on User 1's SVG
INSERT INTO notifications (user_id, actor_id, notification_type, target_type, target_id, content, action_url)
VALUES (1, 3, 'comment', 'svg_image', 'example_1234567890.svg', 'Great diagram! How did you create this?', '/view_svg/example_1234567890.svg#comment-1');

-- Sample notification: User 4 replied to User 1's comment
INSERT INTO notifications (user_id, actor_id, notification_type, target_type, target_id, content, action_url)
VALUES (1, 4, 'reply', 'comment', '5', 'Thanks for the tip!', '/view_svg/example_1234567890.svg#comment-6');

-- Sample notification: User 5 followed User 1
INSERT INTO notifications (user_id, actor_id, notification_type, target_type, target_id, action_url)
VALUES (1, 5, 'follow', 'user', '1', '/profile/user1');

-- Verify sample data
SELECT 
    n.id,
    n.notification_type,
    u1.username AS recipient,
    u2.username AS actor,
    n.target_type,
    n.target_id,
    n.is_read,
    n.created_at
FROM notifications n
JOIN user u1 ON n.user_id = u1.id
JOIN user u2 ON n.actor_id = u2.id
ORDER BY n.created_at DESC;
*/

-- ================================================================
-- Performance Analysis (Run after some data accumulation)
-- ================================================================

/*
-- Check index usage
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    SEQ_IN_INDEX,
    COLUMN_NAME,
    CARDINALITY
FROM information_schema.STATISTICS
WHERE TABLE_SCHEMA = DATABASE()
AND TABLE_NAME = 'notifications'
ORDER BY INDEX_NAME, SEQ_IN_INDEX;

-- Analyze notification distribution
SELECT 
    notification_type,
    COUNT(*) as count,
    SUM(CASE WHEN is_read = TRUE THEN 1 ELSE 0 END) as read_count,
    SUM(CASE WHEN is_read = FALSE THEN 1 ELSE 0 END) as unread_count,
    ROUND(AVG(TIMESTAMPDIFF(SECOND, created_at, COALESCE(read_at, NOW()))), 2) as avg_time_to_read_seconds
FROM notifications
GROUP BY notification_type
ORDER BY count DESC;

-- Find users with most unread notifications
SELECT 
    u.username,
    u.email,
    COUNT(*) as unread_count
FROM notifications n
JOIN user u ON n.user_id = u.id
WHERE n.is_read = FALSE
GROUP BY n.user_id, u.username, u.email
ORDER BY unread_count DESC
LIMIT 10;
*/

-- ================================================================
-- Maintenance Queries
-- ================================================================

/*
-- Clean up old read notifications (older than 90 days)
DELETE FROM notifications 
WHERE is_read = TRUE 
AND created_at < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- Optimize table (run monthly)
ANALYZE TABLE notifications;
OPTIMIZE TABLE notifications;
*/

-- ================================================================
-- Rollback Script (Use only if needed to undo this migration)
-- ================================================================

/*
DROP TABLE IF EXISTS notifications;
*/

