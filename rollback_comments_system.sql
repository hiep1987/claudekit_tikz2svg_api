-- =====================================================
-- COMMENTS SYSTEM - ROLLBACK SCRIPT
-- Version: 1.2.1 Final
-- Date: 2025-10-22
-- Database: tikz2svg_local (MySQL 8.0+)
-- =====================================================
--
-- ⚠️  WARNING: This script will DELETE all comments data!
-- Only run this if you need to completely remove the
-- Comments feature from the database.
--
-- WHAT THIS DOES:
-- - Drops foreign key constraints
-- - Drops svg_comments and svg_comment_likes tables
-- - Removes comments_count column from svg_image
-- - Removes idx_filename from svg_image
--
-- BACKUP FIRST:
-- mysqldump -u user -p tikz2svg_local > backup_before_rollback.sql
-- =====================================================

-- Step 1: Verify database
SELECT 'Starting Comments System Rollback...' AS Status;
SELECT DATABASE() AS CurrentDatabase;

-- =====================================================
-- PHASE 1: Drop Foreign Keys
-- =====================================================

SELECT 'Phase 1: Dropping foreign key constraints...' AS Status;

-- Drop FK from svg_comment_likes to svg_comments
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comment_likes' 
      AND CONSTRAINT_NAME = 'fk_comment_likes_comment'
);

SET @sql = IF(
    @fk_exists > 0,
    'ALTER TABLE svg_comment_likes DROP FOREIGN KEY fk_comment_likes_comment',
    'SELECT ''FK fk_comment_likes_comment does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Drop FK from svg_comment_likes to user
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comment_likes' 
      AND CONSTRAINT_NAME = 'fk_comment_likes_user'
);

SET @sql = IF(
    @fk_exists > 0,
    'ALTER TABLE svg_comment_likes DROP FOREIGN KEY fk_comment_likes_user',
    'SELECT ''FK fk_comment_likes_user does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Drop self-referencing FK in svg_comments
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comments' 
      AND CONSTRAINT_NAME = 'fk_comments_parent'
);

SET @sql = IF(
    @fk_exists > 0,
    'ALTER TABLE svg_comments DROP FOREIGN KEY fk_comments_parent',
    'SELECT ''FK fk_comments_parent does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Drop FK from svg_comments to svg_image
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comments' 
      AND CONSTRAINT_NAME = 'fk_comments_svg_image'
);

SET @sql = IF(
    @fk_exists > 0,
    'ALTER TABLE svg_comments DROP FOREIGN KEY fk_comments_svg_image',
    'SELECT ''FK fk_comments_svg_image does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- Drop FK from svg_comments to user
SET @fk_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_comments' 
      AND CONSTRAINT_NAME = 'fk_comments_user'
);

SET @sql = IF(
    @fk_exists > 0,
    'ALTER TABLE svg_comments DROP FOREIGN KEY fk_comments_user',
    'SELECT ''FK fk_comments_user does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 1: ✅ Foreign keys dropped' AS Status;

-- =====================================================
-- PHASE 2: Drop Tables
-- =====================================================

SELECT 'Phase 2: Dropping tables...' AS Status;

DROP TABLE IF EXISTS svg_comment_likes;
SELECT 'Phase 2a: ✅ svg_comment_likes table dropped' AS Status;

DROP TABLE IF EXISTS svg_comments;
SELECT 'Phase 2b: ✅ svg_comments table dropped' AS Status;

-- =====================================================
-- PHASE 3: Remove Column from svg_image
-- =====================================================

SELECT 'Phase 3: Removing comments_count column...' AS Status;

SET @column_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.COLUMNS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_image' 
      AND COLUMN_NAME = 'comments_count'
);

SET @sql = IF(
    @column_exists > 0,
    'ALTER TABLE svg_image DROP COLUMN comments_count',
    'SELECT ''Column comments_count does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 3: ✅ comments_count column removed' AS Status;

-- =====================================================
-- PHASE 4: Remove Index from svg_image
-- =====================================================

SELECT 'Phase 4: Removing idx_filename index...' AS Status;

SET @index_exists = (
    SELECT COUNT(*) 
    FROM INFORMATION_SCHEMA.STATISTICS 
    WHERE TABLE_SCHEMA = DATABASE() 
      AND TABLE_NAME = 'svg_image' 
      AND INDEX_NAME = 'idx_filename'
);

SET @sql = IF(
    @index_exists > 0,
    'DROP INDEX idx_filename ON svg_image',
    'SELECT ''Index idx_filename does not exist'' AS Message'
);

PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SELECT 'Phase 4: ✅ Index removed' AS Status;

-- =====================================================
-- VERIFICATION: Confirm Rollback
-- =====================================================

SELECT '=============================================' AS '';
SELECT 'ROLLBACK VERIFICATION' AS '';
SELECT '=============================================' AS '';

-- Verify tables are gone
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ svg_comments table DELETED'
        ELSE '❌ svg_comments table STILL EXISTS'
    END AS Status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'svg_comments';

SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ svg_comment_likes table DELETED'
        ELSE '❌ svg_comment_likes table STILL EXISTS'
    END AS Status
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'svg_comment_likes';

-- Verify column is gone
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ comments_count column DELETED'
        ELSE '❌ comments_count column STILL EXISTS'
    END AS Status
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'svg_image' 
  AND COLUMN_NAME = 'comments_count';

-- Verify index is gone
SELECT 
    CASE 
        WHEN COUNT(*) = 0 THEN '✅ idx_filename index DELETED (or never existed)'
        ELSE '❌ idx_filename index STILL EXISTS'
    END AS Status
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = DATABASE() 
  AND TABLE_NAME = 'svg_image' 
  AND INDEX_NAME = 'idx_filename';

-- Final summary
SELECT '=============================================' AS '';
SELECT '✅ ROLLBACK COMPLETED SUCCESSFULLY!' AS Result;
SELECT 'Comments System has been completely removed.' AS Message;
SELECT '=============================================' AS '';

/*
TO RESTORE COMMENTS FEATURE AFTER ROLLBACK:
Run the migration script again:
  mysql -u your_user -p your_database < migrate_comments_system.sql
*/

