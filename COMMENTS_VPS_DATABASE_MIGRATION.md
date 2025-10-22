# Comments Feature - VPS Database Migration Guide

**Date:** 2025-10-22  
**Version:** 1.0  
**Purpose:** Chi tiết migration CSDL từ local lên VPS production  
**⚠️ CRITICAL:** Phải chạy trên VPS production để đồng bộ với local

---

## 🎯 Tổng quan

Tài liệu này hướng dẫn chi tiết cách migrate database cho Comments Feature từ môi trường local lên VPS production.

**Database hiện tại:**
- Local: `tikz2svg_local`
- VPS: `tikz2svg_production` (hoặc tên database production của bạn)

**Thay đổi:**
- 2 tables mới: `svg_comments`, `svg_comment_likes`
- 1 column mới: `svg_image.comments_count`
- Multiple indexes và foreign keys

---

## ⚠️ LƯU Ý QUAN TRỌNG TRƯỚC KHI BẮT ĐẦU

### 1. Backup Production Database (BẮT BUỘC!)

```bash
# SSH vào VPS
ssh your-user@your-vps-ip

# Backup toàn bộ database
mysqldump -u [DB_USER] -p [DB_NAME] > \
  backup_before_comments_$(date +%Y%m%d_%H%M%S).sql

# Verify backup
ls -lh backup_before_comments_*.sql

# Download backup về local (từ máy local)
scp your-user@your-vps-ip:~/backup_before_comments_*.sql ./
```

### 2. Kiểm tra Database Hiện Tại

```bash
# Trên VPS
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "SHOW TABLES;"

# Kiểm tra có tables conflict không
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e \
  "SHOW TABLES LIKE 'svg_comment%';"

# Expected: Không có kết quả (tables chưa tồn tại)
```

### 3. Kiểm tra Current Schema

```bash
# Check svg_image table structure
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "DESCRIBE svg_image;"

# Check if comments_count column exists
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e \
  "SHOW COLUMNS FROM svg_image WHERE Field = 'comments_count';"

# Expected: Không có kết quả (column chưa tồn tại)
```

---

## 📋 MIGRATION SCRIPT - COPY TOÀN BỘ VÀO FILE

### File: `add_comments_system.sql`

```sql
-- ============================================================================
-- COMMENTS SYSTEM DATABASE MIGRATION
-- ============================================================================
-- Version: 1.0
-- Date: 2025-10-22
-- Purpose: Add comments and likes functionality for SVG images
-- 
-- IMPORTANT: 
-- - Run this script on VPS production database
-- - Backup database before running
-- - Test on staging first if available
-- ============================================================================

-- Set variables for safety
SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL,ALLOW_INVALID_DATES';

-- ============================================================================
-- STEP 1: ADD comments_count COLUMN TO svg_image
-- ============================================================================

-- Check if column exists first
SELECT 'Step 1: Adding comments_count column to svg_image...' AS 'Status';

ALTER TABLE `svg_image`
ADD COLUMN `comments_count` INT NOT NULL DEFAULT 0
AFTER `keywords`;

-- Create index for performance
CREATE INDEX `idx_comments_count` ON `svg_image` (`comments_count`);

-- Create index on filename for foreign key
CREATE INDEX `idx_filename` ON `svg_image` (`filename`);

SELECT 'Step 1 completed: comments_count column added' AS 'Status';

-- ============================================================================
-- STEP 2: CREATE svg_comments TABLE
-- ============================================================================

SELECT 'Step 2: Creating svg_comments table...' AS 'Status';

CREATE TABLE IF NOT EXISTS `svg_comments` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `svg_filename` VARCHAR(255) NOT NULL,
  `user_id` INT NOT NULL,
  `user_ip` VARCHAR(45) DEFAULT NULL COMMENT 'IP address for abuse tracking',
  `comment_text` TEXT NOT NULL,
  `content_hash` VARCHAR(64) DEFAULT NULL COMMENT 'SHA256 hash for duplicate detection',
  `parent_comment_id` INT DEFAULT NULL COMMENT 'NULL for top-level, ID for replies',
  `is_edited` TINYINT(1) NOT NULL DEFAULT 0,
  `edited_at` DATETIME DEFAULT NULL,
  `deleted_at` DATETIME DEFAULT NULL COMMENT 'Soft delete timestamp',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` DATETIME DEFAULT NULL COMMENT 'Last modification time',
  `likes_count` INT NOT NULL DEFAULT 0,
  `replies_count` INT NOT NULL DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `idx_svg_filename` (`svg_filename`),
  KEY `idx_parent_comment_id` (`parent_comment_id`),
  KEY `idx_user_ip` (`user_ip`),
  KEY `idx_content_hash` (`content_hash`),
  KEY `idx_created_at_desc` (`created_at` DESC),
  KEY `idx_filename_created_desc` (`svg_filename`, `created_at` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Comments on SVG images with support for replies';

SELECT 'Step 2 completed: svg_comments table created' AS 'Status';

-- ============================================================================
-- STEP 3: CREATE svg_comment_likes TABLE
-- ============================================================================

SELECT 'Step 3: Creating svg_comment_likes table...' AS 'Status';

CREATE TABLE IF NOT EXISTS `svg_comment_likes` (
  `id` INT NOT NULL AUTO_INCREMENT,
  `comment_id` INT NOT NULL,
  `user_id` INT NOT NULL,
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_comment_like` (`comment_id`, `user_id`),
  KEY `idx_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Like tracking for comments';

SELECT 'Step 3 completed: svg_comment_likes table created' AS 'Status';

-- ============================================================================
-- STEP 4: ADD FOREIGN KEY CONSTRAINTS
-- ============================================================================

SELECT 'Step 4: Adding foreign key constraints...' AS 'Status';

-- Foreign key: svg_comments -> svg_image
ALTER TABLE `svg_comments`
ADD CONSTRAINT `fk_comments_svg_filename`
FOREIGN KEY (`svg_filename`) REFERENCES `svg_image` (`filename`)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Foreign key: svg_comments -> user
ALTER TABLE `svg_comments`
ADD CONSTRAINT `fk_comments_user_id`
FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Foreign key: svg_comments -> svg_comments (self-referencing for replies)
ALTER TABLE `svg_comments`
ADD CONSTRAINT `fk_comments_parent_comment`
FOREIGN KEY (`parent_comment_id`) REFERENCES `svg_comments` (`id`)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Foreign key: svg_comment_likes -> svg_comments
ALTER TABLE `svg_comment_likes`
ADD CONSTRAINT `fk_comment_likes_comment`
FOREIGN KEY (`comment_id`) REFERENCES `svg_comments` (`id`)
ON DELETE CASCADE ON UPDATE CASCADE;

-- Foreign key: svg_comment_likes -> user
ALTER TABLE `svg_comment_likes`
ADD CONSTRAINT `fk_comment_likes_user`
FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
ON DELETE CASCADE ON UPDATE CASCADE;

SELECT 'Step 4 completed: Foreign keys added' AS 'Status';

-- ============================================================================
-- STEP 5: VERIFICATION
-- ============================================================================

SELECT 'Step 5: Running verification queries...' AS 'Status';

-- Check tables exist
SELECT 
    COUNT(*) as table_count,
    'Expected: 2 (svg_comments, svg_comment_likes)' as expected
FROM information_schema.tables 
WHERE table_schema = DATABASE()
  AND table_name IN ('svg_comments', 'svg_comment_likes');

-- Check svg_comments columns
SELECT 
    COUNT(*) as column_count,
    'Expected: 14' as expected
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'svg_comments';

-- Check svg_comment_likes columns
SELECT 
    COUNT(*) as column_count,
    'Expected: 4' as expected
FROM information_schema.columns
WHERE table_schema = DATABASE()
  AND table_name = 'svg_comment_likes';

-- Check foreign keys
SELECT 
    COUNT(*) as fk_count,
    'Expected: 5' as expected
FROM information_schema.key_column_usage
WHERE table_schema = DATABASE()
  AND constraint_name LIKE 'fk_comment%';

-- Check indexes on svg_comments
SELECT 
    COUNT(*) as index_count,
    'Expected: At least 6' as expected
FROM information_schema.statistics
WHERE table_schema = DATABASE()
  AND table_name = 'svg_comments';

SELECT 'Step 5 completed: Verification finished' AS 'Status';

-- ============================================================================
-- STEP 6: RESTORE SETTINGS
-- ============================================================================

SET SQL_MODE=@OLD_SQL_MODE;
SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;
SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;

-- ============================================================================
-- MIGRATION COMPLETED SUCCESSFULLY
-- ============================================================================

SELECT '✅ MIGRATION COMPLETED SUCCESSFULLY!' AS 'Final Status';
SELECT 'Please verify the results above.' AS 'Next Step';
SELECT 'If any verification fails, check the output carefully.' AS 'Warning';

-- ============================================================================
-- ROLLBACK INSTRUCTIONS (IF NEEDED)
-- ============================================================================
-- 
-- IF YOU NEED TO ROLLBACK, RUN THESE COMMANDS:
-- 
-- DROP TABLE IF EXISTS `svg_comment_likes`;
-- DROP TABLE IF EXISTS `svg_comments`;
-- ALTER TABLE `svg_image` DROP COLUMN `comments_count`;
-- ALTER TABLE `svg_image` DROP INDEX `idx_comments_count`;
-- ALTER TABLE `svg_image` DROP INDEX `idx_filename`;
-- 
-- THEN RESTORE FROM BACKUP:
-- mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] < backup_before_comments_YYYYMMDD_HHMMSS.sql
-- 
-- ============================================================================
```

---

## 🚀 HƯỚNG DẪN CHẠY MIGRATION TRÊN VPS

### Bước 1: Upload Script lên VPS

**Option A: Tạo file trực tiếp trên VPS**

```bash
# SSH vào VPS
ssh your-user@your-vps-ip

# Navigate to project directory
cd /path/to/your/project

# Tạo file migration
nano add_comments_system.sql

# Paste toàn bộ SQL script ở trên
# Ctrl+X, Y, Enter để save
```

**Option B: Upload từ local**

```bash
# Từ máy local, upload file
scp add_comments_system.sql your-user@your-vps-ip:/path/to/project/
```

### Bước 2: Chạy Migration

```bash
# Trên VPS, chạy migration
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] < add_comments_system.sql

# Example:
# mysql -u tikz_user -p tikz2svg_production < add_comments_system.sql
```

**Expected Output:**

```
Status
Step 1: Adding comments_count column to svg_image...
Step 1 completed: comments_count column added
Step 2: Creating svg_comments table...
Step 2 completed: svg_comments table created
Step 3: Creating svg_comment_likes table...
Step 3 completed: svg_comment_likes table created
Step 4: Adding foreign key constraints...
Step 4 completed: Foreign keys added
Step 5: Running verification queries...
...
✅ MIGRATION COMPLETED SUCCESSFULLY!
```

### Bước 3: Verify Migration

```bash
# Check tables created
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "SHOW TABLES LIKE 'svg_comment%';"

# Expected output:
# svg_comments
# svg_comment_likes

# Check svg_comments structure
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "DESCRIBE svg_comments;"

# Check foreign keys
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    REFERENCED_TABLE_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = '[DB_NAME]'
  AND CONSTRAINT_NAME LIKE 'fk_comment%';
"

# Expected: 5 foreign keys
```

### Bước 4: Test Basic Operations

```bash
# Test insert (sẽ fail vì chưa có user/svg, nhưng shows structure works)
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT COUNT(*) as current_comments FROM svg_comments;
SELECT COUNT(*) as current_likes FROM svg_comment_likes;
"

# Both should return 0
```

---

## 🔄 ROLLBACK PROCEDURE (Nếu cần)

### Khi nào cần rollback?

- Migration failed with errors
- Foreign key constraints có vấn đề
- Phát hiện lỗi sau khi chạy

### Rollback Script

**File: `rollback_comments_system.sql`**

```sql
-- ============================================================================
-- ROLLBACK COMMENTS SYSTEM MIGRATION
-- ============================================================================
-- WARNING: This will DELETE all comments data!
-- Only use if migration failed or needs to be redone
-- ============================================================================

SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;

SELECT 'Starting rollback...' AS 'Status';

-- Step 1: Drop foreign keys first
ALTER TABLE `svg_comment_likes` DROP FOREIGN KEY IF EXISTS `fk_comment_likes_comment`;
ALTER TABLE `svg_comment_likes` DROP FOREIGN KEY IF EXISTS `fk_comment_likes_user`;
ALTER TABLE `svg_comments` DROP FOREIGN KEY IF EXISTS `fk_comments_svg_filename`;
ALTER TABLE `svg_comments` DROP FOREIGN KEY IF EXISTS `fk_comments_user_id`;
ALTER TABLE `svg_comments` DROP FOREIGN KEY IF EXISTS `fk_comments_parent_comment`;

SELECT 'Foreign keys dropped' AS 'Status';

-- Step 2: Drop tables
DROP TABLE IF EXISTS `svg_comment_likes`;
DROP TABLE IF EXISTS `svg_comments`;

SELECT 'Tables dropped' AS 'Status';

-- Step 3: Remove columns from svg_image
ALTER TABLE `svg_image` DROP INDEX IF EXISTS `idx_comments_count`;
ALTER TABLE `svg_image` DROP INDEX IF EXISTS `idx_filename`;
ALTER TABLE `svg_image` DROP COLUMN IF EXISTS `comments_count`;

SELECT 'svg_image columns removed' AS 'Status';

SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;

SELECT '✅ ROLLBACK COMPLETED' AS 'Final Status';
SELECT 'You can now restore from backup or re-run migration' AS 'Next Step';
```

### Chạy Rollback

```bash
# Tạo rollback script
nano rollback_comments_system.sql
# Paste script ở trên

# Chạy rollback
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] < rollback_comments_system.sql

# Restore from backup (if needed)
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] < backup_before_comments_YYYYMMDD_HHMMSS.sql
```

---

## 📊 POST-MIGRATION VERIFICATION CHECKLIST

Sau khi chạy migration thành công, verify các điểm sau:

### Database Structure

```bash
# 1. Tables exist
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT table_name, table_rows, 
       ROUND(data_length/1024/1024, 2) as 'Size_MB'
FROM information_schema.tables
WHERE table_schema = '[DB_NAME]'
  AND table_name IN ('svg_comments', 'svg_comment_likes', 'svg_image')
ORDER BY table_name;
"
```

**Expected:**
- ✅ svg_comments: 0 rows, ~0 MB
- ✅ svg_comment_likes: 0 rows, ~0 MB
- ✅ svg_image: existing rows, existing size

### Column Verification

```bash
# 2. Check svg_image has new column
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SHOW COLUMNS FROM svg_image WHERE Field IN ('comments_count', 'filename');
"
```

**Expected:**
- ✅ comments_count: INT, Default 0
- ✅ filename: VARCHAR(255)

### Index Verification

```bash
# 3. Check indexes
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT 
    TABLE_NAME,
    INDEX_NAME,
    GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX) as COLUMNS
FROM INFORMATION_SCHEMA.STATISTICS
WHERE TABLE_SCHEMA = '[DB_NAME]'
  AND TABLE_NAME IN ('svg_image', 'svg_comments', 'svg_comment_likes')
  AND INDEX_NAME LIKE 'idx_%'
GROUP BY TABLE_NAME, INDEX_NAME
ORDER BY TABLE_NAME, INDEX_NAME;
"
```

**Expected:**
- ✅ svg_image: idx_filename, idx_comments_count
- ✅ svg_comments: idx_svg_filename, idx_parent_comment_id, idx_user_ip, idx_content_hash, idx_created_at_desc, idx_filename_created_desc
- ✅ svg_comment_likes: idx_user_id

### Foreign Key Verification

```bash
# 4. Check foreign keys
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = '[DB_NAME]'
  AND CONSTRAINT_NAME LIKE 'fk_comment%'
ORDER BY CONSTRAINT_NAME;
"
```

**Expected: 5 foreign keys**
- ✅ fk_comments_svg_filename
- ✅ fk_comments_user_id
- ✅ fk_comments_parent_comment
- ✅ fk_comment_likes_comment
- ✅ fk_comment_likes_user

---

## 🔐 SECURITY CONSIDERATIONS

### 1. Database User Permissions

Ensure database user has necessary permissions:

```sql
-- Check current permissions
SHOW GRANTS FOR '[DB_USER]'@'localhost';

-- Should have at least:
-- SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, INDEX, REFERENCES
```

### 2. Backup Retention

```bash
# Keep backups for at least 30 days
# Compress old backups
gzip backup_before_comments_20251022_*.sql

# Archive
mkdir -p ~/database_backups/2025-10
mv backup_before_comments_*.sql.gz ~/database_backups/2025-10/
```

### 3. Monitor Migration

```bash
# Check MySQL error log during migration
tail -f /var/log/mysql/error.log

# Check slow queries (should be none for migration)
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT * FROM mysql.slow_log 
WHERE sql_text LIKE '%svg_comment%' 
ORDER BY start_time DESC LIMIT 10;
"
```

---

## 📝 CHANGELOG

### Version 1.0 (2025-10-22)

**Added:**
- `svg_comments` table with 14 columns
- `svg_comment_likes` table with 4 columns
- `svg_image.comments_count` column (INT, default 0)
- 6 indexes on `svg_comments`
- 1 index on `svg_comment_likes`
- 2 indexes on `svg_image` (idx_filename, idx_comments_count)
- 5 foreign key constraints

**Purpose:**
- Enable commenting on SVG images
- Support nested replies (1 level)
- Like/unlike functionality
- Spam detection (via user_ip, content_hash)
- Performance optimization (indexes)

---

## 🆘 TROUBLESHOOTING

### Error: "Table already exists"

```bash
# Check if table exists
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "SHOW TABLES LIKE 'svg_comments';"

# If exists, either:
# 1. Drop and recreate (loses data!)
# 2. Skip creation (if structure matches)
# 3. Use rollback script first
```

### Error: "Foreign key constraint fails"

```bash
# Check referenced tables exist
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SELECT table_name FROM information_schema.tables
WHERE table_schema = '[DB_NAME]'
  AND table_name IN ('svg_image', 'user');
"

# Both should exist, if not, migration will fail
```

### Error: "Column already exists"

```bash
# Check if comments_count exists
mysql -u [DB_USER] -p[DB_PASSWORD] [DB_NAME] -e "
SHOW COLUMNS FROM svg_image WHERE Field = 'comments_count';
"

# If exists, remove it first or skip that step
```

---

## 📞 NEXT STEPS AFTER MIGRATION

1. ✅ Verify migration successful (all checks pass)
2. ✅ Deploy updated application code to VPS
3. ✅ Test commenting functionality on production
4. ✅ Monitor database performance
5. ✅ Keep backup for 30+ days

---

**Last Updated:** 2025-10-22  
**Status:** Ready for VPS deployment  
**Tested on:** tikz2svg_local (MySQL 8.0+)  
**Ready for:** tikz2svg_production on VPS

**⚠️ REMEMBER:** Always backup before migration!

