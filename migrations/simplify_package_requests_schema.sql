-- SIMPLIFY PACKAGE_REQUESTS SCHEMA MIGRATION
-- ============================================
-- Rút gọn bảng package_requests để phù hợp với schema mới
-- Created: 2025-10-30

-- 1. Backup current table
CREATE TABLE package_requests_backup AS SELECT * FROM package_requests;

-- 2. Create new simplified table
DROP TABLE IF EXISTS package_requests_new;

CREATE TABLE package_requests_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL,
    justification TEXT NOT NULL,
    use_case_example TEXT DEFAULT NULL,
    requester_name VARCHAR(100) NOT NULL,
    requester_email VARCHAR(255) NOT NULL,
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('pending', 'under_review', 'approved', 'rejected', 'implemented') DEFAULT 'pending',
    admin_notes TEXT DEFAULT NULL,
    reviewed_by_email VARCHAR(255) DEFAULT NULL,
    reviewed_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_package_name (package_name),
    INDEX idx_requester_email (requester_email),
    INDEX idx_status (status),
    INDEX idx_priority (priority),
    INDEX idx_created_at (created_at)
);

-- 3. Migrate existing data - copy essential columns only
INSERT INTO package_requests_new (
    id, package_name, justification, use_case_example, 
    requester_name, requester_email, priority, status,
    admin_notes, reviewed_by_email, reviewed_at, created_at, updated_at
)
SELECT 
    id, package_name, justification, use_case_example,
    requester_name, requester_email, priority, status,
    admin_notes, reviewed_by_email, reviewed_at, created_at, updated_at
FROM package_requests;

-- 4. Handle foreign key constraints before replacing table
-- Temporarily disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Replace original table
DROP TABLE package_requests;
RENAME TABLE package_requests_new TO package_requests;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- 5. Update package_changelog to remove references to deleted columns
-- Clean up any changelog entries that reference old column structure
UPDATE package_changelog 
SET new_values = JSON_REMOVE(
    new_values, 
    '$.package_type',
    '$.description', 
    '$.documentation_url',
    '$.requester_user_id'
)
WHERE new_values IS NOT NULL;

-- 6. Add summary comment to changelog
INSERT INTO package_changelog (
    package_name, 
    action_type, 
    new_values, 
    changed_by_email, 
    change_reason
) VALUES (
    'SCHEMA_MIGRATION_REQUESTS', 
    'updated', 
    '{"schema": "simplified_requests", "removed_columns": ["package_type", "description", "documentation_url", "requester_user_id"]}',
    'admin@tikz2svg.com',
    'Simplified package_requests schema: removed 4 unused columns'
);

-- 7. Verify results
SELECT 
    'Migration Results' as summary,
    COUNT(*) as total_requests,
    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending_requests,
    SUM(CASE WHEN status = 'approved' THEN 1 ELSE 0 END) as approved_requests,
    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected_requests
FROM package_requests;

-- 8. Show simplified schema
DESCRIBE package_requests;
