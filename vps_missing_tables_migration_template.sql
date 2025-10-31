-- =====================================================
-- VPS MISSING TABLES MIGRATION
-- =====================================================
-- Date: 2025-10-31
-- Purpose: Add 4 missing tables to VPS
-- Tables: compilation_metrics, rate_limit_tracking, svg_views
-- =====================================================

-- Backup first!
-- mysqldump -u root -p tikz2svg > backup_$(date +%Y%m%d).sql

-- Check current database
SELECT DATABASE() as current_db;

-- =====================================================
-- TODO: Add CREATE TABLE statements below
-- Export from local: 
-- mysqldump -u hiep1987 tikz2svg_local --no-data --tables [table_names] > export.sql
-- =====================================================


-- Table: compilation_metrics
-- TODO: Replace with actual schema from local database
CREATE TABLE IF NOT EXISTS `compilation_metrics` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Add columns here
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Table: rate_limit_tracking
-- TODO: Replace with actual schema from local database
CREATE TABLE IF NOT EXISTS `rate_limit_tracking` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Add columns here
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- Table: svg_views
-- TODO: Replace with actual schema from local database
CREATE TABLE IF NOT EXISTS `svg_views` (
    id INT AUTO_INCREMENT PRIMARY KEY,
    -- Add columns here
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- =====================================================
-- VERIFICATION
-- =====================================================

-- Check all tables exist
SHOW TABLES;

-- Count tables (should be 21 after migration)
SELECT COUNT(*) as total_tables 
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE();

-- Verify specific tables
SELECT COUNT(*) as compilation_metrics_count FROM `compilation_metrics`;
SELECT COUNT(*) as rate_limit_tracking_count FROM `rate_limit_tracking`;
SELECT COUNT(*) as svg_views_count FROM `svg_views`;
