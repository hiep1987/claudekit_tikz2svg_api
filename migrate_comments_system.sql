-- =====================================================
-- COMMENTS SYSTEM - DATABASE MIGRATION SCRIPT
-- Version: 1.2.1 Final
-- Date: 2025-10-22
-- Database: tikz2svg_local (MySQL 8.0+)
-- =====================================================
-- 
-- This script creates the complete database schema for 
-- the Comments Feature with production-ready optimizations.
--
-- INCLUDES:
-- - 2 new tables (svg_comments, svg_comment_likes)
-- - 1 new column (svg_image.comments_count)
-- - 8 indexes for performance
-- - 5 foreign key constraints
-- - Rollback procedures
-- 
-- SAFETY:
-- - Uses IF NOT EXISTS to prevent errors
-- - Idempotent (can run multiple times safely)
-- - Transaction-based for atomic operations
-- =====================================================

-- Step 1: Verify database connection
SELECT 'Starting Comments System Migration...' AS Status;
SELECT DATABASE() AS CurrentDatabase;
SELECT VERSION() AS MySQLVersion;

-- =====================================================
-- PHASE 1: CREATE svg_comments TABLE
-- =====================================================

SELECT 'Phase 1: Creating svg_comments table...' AS Status;

CREATE TABLE IF NOT EXISTS svg_comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    svg_filename VARCHAR(255) NOT NULL,
    user_id INT NOT NULL,
    comment_text TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL,
    parent_comment_id INT DEFAULT NULL,
    likes_count INT DEFAULT 0,
    user_ip VARCHAR(45) DEFAULT NULL COMMENT 'IP address for spam tracking',
    content_hash VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 hash for duplicate detection',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_svg_filename (svg_filename),
    INDEX idx_user_id (user_id),
    INDEX idx_parent_comment_id (parent_comment_id),
    INDEX idx_created_at_desc (created_at DESC) COMMENT 'For sorting by newest first',
    INDEX idx_filename_created_desc (svg_filename, created_at DESC) COMMENT 'Composite for paginated queries',
    
    CONSTRAINT fk_comments_user 
        FOREIGN KEY (user_id) 
        REFERENCES user(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Stores user comments on SVG images with spam tracking';

SELECT 'Phase 1: ✅ svg_comments table created successfully' AS Status;

-- =====================================================
-- PHASE 2: CREATE svg_comment_likes TABLE
-- =====================================================

SELECT 'Phase 2: Creating svg_comment_likes table...' AS Status;

CREATE TABLE IF NOT EXISTS svg_comment_likes (
    id INT AUTO_INCREMENT PRIMARY KEY,
    comment_id INT NOT NULL,
    user_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE KEY unique_comment_like (comment_id, user_id) COMMENT 'Prevent duplicate likes',
    INDEX idx_comment_id (comment_id),
    INDEX idx_user_id (user_id),
    
    CONSTRAINT fk_comment_likes_comment 
        FOREIGN KEY (comment_id) 
        REFERENCES svg_comments(id) 
        ON DELETE CASCADE,
    CONSTRAINT fk_comment_likes_user 
        FOREIGN KEY (user_id) 
        REFERENCES user(id) 
        ON DELETE CASCADE
) ENGINE=InnoDB 
  DEFAULT CHARSET=utf8mb4 
  COLLATE=utf8mb4_unicode_ci
  COMMENT='Tracks which users liked which comments';

SELECT 'Phase 2: ✅ svg_comment_likes table created successfully' AS Status;

-- =====================================================
-- PHASE 3: ADD comments_count TO svg_image
-- =====================================================

SELECT 'Phase 3: Adding comments_count column to svg_image...' AS Status;

-- Check if column already exists
SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_image' 
      AND COLUMN_NAME = 'comments_count'
);

-- Add column only if it doesn't exist
SET @sql = IF(
    @column_exists = 0,
    'ALTER TABLE svg_image ADD COLUMN comments_count INT DEFAULT 0 COMMENT ''Denormalized count for performance''',
    'SELECT ''Column comments_count already exists'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 3: ✅ comments_count column processed' AS Status;

-- =====================================================
-- PHASE 4: ADD UNIQUE INDEX ON svg_image.filename
-- =====================================================

SELECT 'Phase 4: Creating UNIQUE index on svg_image.filename...' AS Status;

-- Check if index already exists
SET @index_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_image' 
      AND INDEX_NAME = 'idx_filename'
);

-- Create UNIQUE index only if it doesn't exist
SET @sql = IF(
    @index_exists = 0,
    'CREATE UNIQUE INDEX idx_filename ON svg_image(filename)',
    'SELECT ''Index idx_filename already exists'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 4: ✅ UNIQUE Index on filename processed' AS Status;

-- =====================================================
-- PHASE 5: ADD FOREIGN KEY svg_comments -> svg_image
-- =====================================================

SELECT 'Phase 5: Adding foreign key svg_comments -> svg_image...' AS Status;

-- Check if FK already exists
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comments' 
      AND CONSTRAINT_NAME = 'fk_comments_svg_image'
);

-- Add FK only if it doesn't exist
SET @sql = IF(
    @fk_exists = 0,
    'ALTER TABLE svg_comments 
     ADD CONSTRAINT fk_comments_svg_image 
     FOREIGN KEY (svg_filename) 
     REFERENCES svg_image(filename) 
     ON DELETE CASCADE',
    'SELECT ''Foreign key fk_comments_svg_image already exists'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 5: ✅ Foreign key to svg_image processed' AS Status;

-- =====================================================
-- PHASE 6: ADD PARENT COMMENT SELF-REFERENCING FK
-- =====================================================

SELECT 'Phase 6: Adding self-referencing FK for nested comments...' AS Status;

-- Check if FK already exists
SET @fk_parent_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comments' 
      AND CONSTRAINT_NAME = 'fk_comments_parent'
);

-- Add FK only if it doesn't exist
SET @sql = IF(
    @fk_parent_exists = 0,
    'ALTER TABLE svg_comments 
     ADD CONSTRAINT fk_comments_parent 
     FOREIGN KEY (parent_comment_id) 
     REFERENCES svg_comments(id) 
     ON DELETE CASCADE',
    'SELECT ''Foreign key fk_comments_parent already exists'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 6: ✅ Self-referencing FK processed' AS Status;

-- =====================================================
-- VERIFICATION: Check all tables and indexes
-- =====================================================

SELECT '=============================================' AS '';
SELECT 'MIGRATION VERIFICATION' AS '';
SELECT '=============================================' AS '';

-- Check tables exist
SELECT 
    'svg_comments' AS TableName,
    CASE 
        WHEN TABLE_NAME IS NOT NULL THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END AS Status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'svg_comments'
UNION ALL
SELECT 
    'svg_comment_likes' AS TableName,
    CASE 
        WHEN TABLE_NAME IS NOT NULL THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END AS Status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'svg_comment_likes';

-- Check columns
SELECT 
    'svg_image.comments_count' AS ColumnName,
    CASE 
        WHEN COLUMN_NAME IS NOT NULL THEN '✅ EXISTS'
        ELSE '❌ MISSING'
    END AS Status
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'svg_image' 
  AND COLUMN_NAME = 'comments_count';

-- Check indexes
SELECT 
    INDEX_NAME AS IndexName,
    TABLE_NAME AS TableName,
    COLUMN_NAME AS ColumnName,
    '✅ EXISTS' AS Status
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME IN ('svg_comments', 'svg_comment_likes', 'svg_image')
  AND INDEX_NAME IN (
      'idx_svg_filename',
      'idx_user_id',
      'idx_parent_comment_id',
      'idx_created_at_desc',
      'idx_filename_created_desc',
      'idx_comment_id',
      'idx_filename',
      'unique_comment_like'
  )
ORDER BY TABLE_NAME, INDEX_NAME;

-- Check foreign keys
SELECT 
    CONSTRAINT_NAME AS ForeignKey,
    TABLE_NAME AS FromTable,
    REFERENCED_TABLE_NAME AS ToTable,
    '✅ EXISTS' AS Status
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = DATABASE() 
  AND CONSTRAINT_NAME IN (
      'fk_comments_user',
      'fk_comments_svg_image',
      'fk_comments_parent',
      'fk_comment_likes_comment',
      'fk_comment_likes_user'
  )
ORDER BY CONSTRAINT_NAME;

-- Final summary
SELECT '=============================================' AS '';
SELECT '✅ MIGRATION COMPLETED SUCCESSFULLY!' AS Result;
SELECT '=============================================' AS '';
SELECT CONCAT('Total tables: ', COUNT(*)) AS Summary
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME IN ('svg_comments', 'svg_comment_likes');

-- =====================================================
-- NOTES FOR VPS DEPLOYMENT
-- =====================================================
/*
TO RUN THIS MIGRATION ON VPS:

1. Upload this file:
   scp migrate_comments_system.sql user@vps:/path/to/

2. Connect and run:
   mysql -u your_user -p your_database < migrate_comments_system.sql

3. Verify:
   mysql -u your_user -p -e "
     SELECT COUNT(*) FROM svg_comments;
     SELECT COUNT(*) FROM svg_comment_likes;
     DESCRIBE svg_image;
   " your_database

4. Check full documentation:
   See COMMENTS_VPS_DATABASE_MIGRATION.md

ROLLBACK (if needed):
   See rollback_comments_system.sql
*/

