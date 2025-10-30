-- SIMPLIFY PACKAGES SCHEMA MIGRATION
-- ===================================
-- Rút gọn bảng supported_packages và cập nhật status logic
-- Created: 2025-10-30

-- 1. Backup current table
CREATE TABLE supported_packages_backup AS SELECT * FROM supported_packages;

-- 2. Create new simplified table
DROP TABLE IF EXISTS supported_packages_new;

CREATE TABLE supported_packages_new (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(255) NOT NULL UNIQUE,
    status ENUM('active', 'manual') NOT NULL DEFAULT 'manual',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_package_name (package_name),
    INDEX idx_status (status)
);

-- 3. Insert data with new status logic
-- Packages that are in TEX_TEMPLATE = 'active' (có sẵn, không cần %!<..>)
-- Other packages = 'manual' (cần thêm %!<..>)

-- LaTeX packages có sẵn trong TEX_TEMPLATE
INSERT INTO supported_packages_new (package_name, status) VALUES
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
('tkz-tab', 'active');

-- TikZ libraries có sẵn trong TEX_TEMPLATE
INSERT INTO supported_packages_new (package_name, status) VALUES
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
('backgrounds', 'active');

-- PGFPlots libraries có sẵn trong TEX_TEMPLATE
INSERT INTO supported_packages_new (package_name, status) VALUES
('polar', 'active');

-- 4. Insert remaining packages as 'manual' (cần %!<..>)
INSERT INTO supported_packages_new (package_name, status)
SELECT package_name, 'manual'
FROM supported_packages
WHERE package_name NOT IN (
    'fontspec', 'amsmath', 'amssymb', 'amsfonts', 'xcolor', 'graphicx',
    'tikz', 'tikz-3dplot', 'pgfplots', 'tkz-euclide', 'tkz-tab',
    'calc', 'math', 'positioning', 'arrows.meta', 'intersections', 'angles',
    'quotes', 'decorations.markings', 'decorations.pathreplacing', 'decorations.text',
    'patterns', 'patterns.meta', 'shadings', 'hobby', 'spy', 'backgrounds',
    'polar'
)
AND status = 'active';

-- 5. Handle foreign key constraints before replacing table
-- Temporarily disable foreign key checks
SET FOREIGN_KEY_CHECKS = 0;

-- Replace original table
DROP TABLE supported_packages;
RENAME TABLE supported_packages_new TO supported_packages;

-- Re-enable foreign key checks
SET FOREIGN_KEY_CHECKS = 1;

-- 6. Update package_requests foreign key reference if needed
-- (Check if there are any foreign key constraints pointing to supported_packages)

-- 7. Clean up package_changelog to remove references to deleted columns
-- Keep only essential changelog entries
DELETE FROM package_changelog WHERE action_type NOT IN ('added', 'updated', 'removed');

-- 8. Add summary comment
INSERT INTO package_changelog (
    package_name, 
    action_type, 
    new_values, 
    changed_by_email, 
    change_reason
) VALUES (
    'SCHEMA_MIGRATION', 
    'updated', 
    '{"schema": "simplified", "active_packages": 28, "manual_packages": "52+"}',
    'admin@tikz2svg.com',
    'Simplified schema: active (có sẵn trong TEX_TEMPLATE) vs manual (cần %!<..>)'
);

-- 9. Verify results
SELECT 
    status,
    COUNT(*) as count,
    GROUP_CONCAT(package_name ORDER BY package_name SEPARATOR ', ') as packages
FROM supported_packages 
GROUP BY status
ORDER BY status;

SELECT 
    'Migration completed' as message,
    COUNT(*) as total_packages,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_packages,
    SUM(CASE WHEN status = 'manual' THEN 1 ELSE 0 END) as manual_packages
FROM supported_packages;
