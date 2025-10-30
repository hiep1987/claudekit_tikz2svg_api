-- =====================================================
-- VPS PACKAGE MANAGEMENT SYSTEM MIGRATION
-- =====================================================
-- Target: VPS Production Database (tikz2svg)
-- Date: October 30, 2025
-- Purpose: Add package management tables to VPS
--
-- INSTRUCTIONS FOR MANUAL EXECUTION ON VPS:
-- 1. SSH to VPS
-- 2. Connect to MySQL: mysql -u root -p tikz2svg
-- 3. Copy and paste this entire script
-- 4. Verify results at the end
-- =====================================================

-- Check current database
SELECT 
    DATABASE() as current_database,
    NOW() as migration_started;

-- =====================================================
-- TABLE 1: supported_packages (SIMPLIFIED SCHEMA)
-- =====================================================

CREATE TABLE IF NOT EXISTS `supported_packages` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `package_name` VARCHAR(255) NOT NULL UNIQUE,
    `status` ENUM('active', 'manual') NOT NULL DEFAULT 'manual',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX `idx_package_name` (`package_name`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Simplified schema: active (có sẵn trong TEX_TEMPLATE) vs manual (cần %!<..>)';

-- =====================================================
-- TABLE 2: package_requests (SIMPLIFIED SCHEMA)
-- =====================================================

CREATE TABLE IF NOT EXISTS `package_requests` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `package_name` VARCHAR(255) NOT NULL,
    `justification` TEXT NOT NULL COMMENT 'Lý do cần package này',
    `use_case_example` TEXT DEFAULT NULL COMMENT 'Ví dụ sử dụng',
    
    -- Requester information
    `requester_name` VARCHAR(100) NOT NULL,
    `requester_email` VARCHAR(255) NOT NULL,
    
    -- Request metadata
    `priority` ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    `status` ENUM('pending', 'under_review', 'approved', 'rejected', 'implemented') DEFAULT 'pending',
    
    -- Admin response
    `admin_notes` TEXT DEFAULT NULL COMMENT 'Ghi chú của admin',
    `reviewed_by_email` VARCHAR(255) DEFAULT NULL,
    `reviewed_at` TIMESTAMP NULL DEFAULT NULL,
    
    -- Timestamps
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX `idx_package_name` (`package_name`),
    INDEX `idx_requester_email` (`requester_email`),
    INDEX `idx_status` (`status`),
    INDEX `idx_priority` (`priority`),
    INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Simplified schema: removed package_type, description, documentation_url';

-- =====================================================
-- TABLE 3: package_changelog
-- =====================================================

CREATE TABLE IF NOT EXISTS `package_changelog` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `package_name` VARCHAR(255) NOT NULL,
    `action_type` ENUM('added', 'updated', 'removed', 'approved', 'rejected') NOT NULL,
    `old_values` JSON DEFAULT NULL COMMENT 'Giá trị cũ (nếu có)',
    `new_values` JSON DEFAULT NULL COMMENT 'Giá trị mới',
    `changed_by_email` VARCHAR(255) NOT NULL COMMENT 'Admin email',
    `change_reason` TEXT DEFAULT NULL COMMENT 'Lý do thay đổi',
    `request_id` INT DEFAULT NULL COMMENT 'Link to package_requests',
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX `idx_package_name` (`package_name`),
    INDEX `idx_action_type` (`action_type`),
    INDEX `idx_changed_by` (`changed_by_email`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_request_id` (`request_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Changelog cho mọi thay đổi về packages';

-- =====================================================
-- POPULATE DATA: Active Packages (có sẵn trong TEX_TEMPLATE)
-- =====================================================

-- LaTeX packages có sẵn (11 packages)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('fontspec', 'active'),
('amsmath', 'active'),
('amssymb', 'active'),
('amsfonts', 'active'),
('xcolor', 'active'),
('graphicx', 'active'),
('tikz', 'active'),
('tikz-3dplot', 'active'),
('pgfplots', 'active'),
('tkz-euclide', 'active'),
('tkz-tab', 'active')
ON DUPLICATE KEY UPDATE 
    `status` = VALUES(`status`),
    `updated_at` = CURRENT_TIMESTAMP;

-- TikZ libraries có sẵn (16 libraries)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('calc', 'active'),
('math', 'active'),
('positioning', 'active'),
('arrows.meta', 'active'),
('intersections', 'active'),
('angles', 'active'),
('quotes', 'active'),
('decorations.markings', 'active'),
('decorations.pathreplacing', 'active'),
('decorations.text', 'active'),
('patterns', 'active'),
('patterns.meta', 'active'),
('shadings', 'active'),
('hobby', 'active'),
('spy', 'active'),
('backgrounds', 'active')
ON DUPLICATE KEY UPDATE 
    `status` = VALUES(`status`),
    `updated_at` = CURRENT_TIMESTAMP;

-- PGFPlots library có sẵn (1 library)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('polar', 'active')
ON DUPLICATE KEY UPDATE 
    `status` = VALUES(`status`),
    `updated_at` = CURRENT_TIMESTAMP;

-- =====================================================
-- POPULATE DATA: Manual Packages (cần %!<..>)
-- =====================================================

-- Popular LaTeX packages (17 packages)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('geometry', 'manual'),
('babel', 'manual'),
('polyglossia', 'manual'),
('microtype', 'manual'),
('hyperref', 'manual'),
('cleveref', 'manual'),
('siunitx', 'manual'),
('booktabs', 'manual'),
('multirow', 'manual'),
('longtable', 'manual'),
('enumitem', 'manual'),
('fancyhdr', 'manual'),
('titlesec', 'manual'),
('listings', 'manual'),
('algorithm2e', 'manual'),
('amsthm', 'manual'),
('mathtools', 'manual')
ON DUPLICATE KEY UPDATE 
    `package_name` = VALUES(`package_name`);

-- TikZ libraries thêm (18 libraries)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('arrows', 'manual'),
('automata', 'manual'),
('trees', 'manual'),
('chains', 'manual'),
('matrix', 'manual'),
('shapes', 'manual'),
('shapes.geometric', 'manual'),
('shapes.symbols', 'manual'),
('shapes.multipart', 'manual'),
('mindmap', 'manual'),
('calendar', 'manual'),
('fit', 'manual'),
('through', 'manual'),
('folding', 'manual'),
('fadings', 'manual'),
('shadows', 'manual'),
('plotmarks', 'manual'),
('circuits', 'manual')
ON DUPLICATE KEY UPDATE 
    `package_name` = VALUES(`package_name`);

-- PGFPlots libraries thêm (8 libraries)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('statistics', 'manual'),
('colormaps', 'manual'),
('dateplot', 'manual'),
('groupplots', 'manual'),
('smithchart', 'manual'),
('ternary', 'manual'),
('fillbetween', 'manual'),
('patchplots', 'manual')
ON DUPLICATE KEY UPDATE 
    `package_name` = VALUES(`package_name`);

-- Other specialized packages (9 packages)
INSERT INTO `supported_packages` (`package_name`, `status`) VALUES
('tkz-base', 'manual'),
('tkz-fct', 'manual'),
('tkz-graph', 'manual'),
('tkz-berge', 'manual'),
('circuitikz', 'manual'),
('tikz-cd', 'manual'),
('tikz-feynman', 'manual'),
('pgf-pie', 'manual'),
('pgfgantt', 'manual')
ON DUPLICATE KEY UPDATE 
    `package_name` = VALUES(`package_name`);

-- =====================================================
-- ADD INITIAL CHANGELOG ENTRY
-- =====================================================

INSERT INTO `package_changelog` (
    `package_name`, 
    `action_type`, 
    `new_values`, 
    `changed_by_email`, 
    `change_reason`
) VALUES (
    'SYSTEM_INITIALIZATION', 
    'added', 
    JSON_OBJECT(
        'schema_version', '1.0',
        'active_packages', 28,
        'manual_packages', 52,
        'total_packages', 80,
        'migration_date', NOW()
    ),
    'quochiep0504@gmail.com',
    'Initial package management system setup on VPS production'
);

-- =====================================================
-- VERIFICATION QUERIES
-- =====================================================

-- Check table creation
SELECT 
    'Tables Created' as verification_step,
    COUNT(*) as tables_count
FROM information_schema.TABLES 
WHERE TABLE_SCHEMA = DATABASE() 
    AND TABLE_NAME IN ('supported_packages', 'package_requests', 'package_changelog');

-- Count packages by status
SELECT 
    'Package Count by Status' as report_type,
    status,
    COUNT(*) as count
FROM `supported_packages` 
GROUP BY status
ORDER BY status;

-- Show active packages (có sẵn trong TEX_TEMPLATE)
SELECT 
    'Active Packages (in TEX_TEMPLATE)' as category,
    GROUP_CONCAT(package_name ORDER BY package_name SEPARATOR ', ') as packages
FROM `supported_packages` 
WHERE status = 'active';

-- Show manual packages count
SELECT 
    'Manual Packages (need %!<..>)' as category,
    COUNT(*) as count
FROM `supported_packages` 
WHERE status = 'manual';

-- Check changelog
SELECT 
    'Changelog Entries' as report_type,
    COUNT(*) as total_entries
FROM `package_changelog`;

-- Final summary
SELECT 
    'Migration Summary' as report_type,
    (SELECT COUNT(*) FROM `supported_packages`) as total_packages,
    (SELECT COUNT(*) FROM `supported_packages` WHERE status = 'active') as active_packages,
    (SELECT COUNT(*) FROM `supported_packages` WHERE status = 'manual') as manual_packages,
    (SELECT COUNT(*) FROM `package_requests`) as total_requests,
    (SELECT COUNT(*) FROM `package_changelog`) as changelog_entries,
    NOW() as migration_completed;

-- =====================================================
-- SUCCESS MESSAGE
-- =====================================================

SELECT 
    '✅ MIGRATION COMPLETED SUCCESSFULLY!' as status,
    'Package Management System is ready on VPS' as message,
    '• 28 active packages (có sẵn trong TEX_TEMPLATE)' as info1,
    '• 52 manual packages (cần thêm %!<..>)' as info2,
    '• 3 tables created: supported_packages, package_requests, package_changelog' as info3,
    '• Ready for production use' as info4;

-- =====================================================
-- NEXT STEPS
-- =====================================================
/*
✅ HOÀN TẤT MIGRATION! 

📋 KIỂM TRA:
1. Xem danh sách packages:
   SELECT * FROM supported_packages ORDER BY status, package_name;

2. Kiểm tra requests (nếu có):
   SELECT * FROM package_requests ORDER BY created_at DESC;

3. Xem changelog:
   SELECT * FROM package_changelog ORDER BY created_at DESC;

🚀 SỬ DỤNG:
- Frontend: http://tikz2svg.com/packages
- Request form: http://tikz2svg.com/packages/request
- Admin panel: http://tikz2svg.com/admin/packages (chỉ cho quochiep0504@gmail.com)

📊 THỐNG KÊ:
- Active packages (28): Không cần %!<..> - đã có sẵn trong TEX_TEMPLATE
- Manual packages (52): Cần thêm %!<\usepackage{...}> hoặc %!<\usetikzlibrary{...}>

🔐 ADMIN:
- Chỉ email: quochiep0504@gmail.com có quyền truy cập admin panel
- Có thể approve/reject package requests
- Có thể sửa tên package nếu user nhập sai

✨ DONE!
*/

