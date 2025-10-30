-- =====================================================
-- PACKAGE MANAGEMENT SYSTEM DATABASE MIGRATION - FIXED
-- =====================================================
-- Version: 1.1
-- Date: Phase 1 Implementation  
-- Purpose: Create package management tables and indexes (Fixed version)

-- =====================================================
-- 1. SUPPORTED PACKAGES TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS supported_packages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(100) NOT NULL UNIQUE,
    package_type ENUM('latex_package', 'tikz_library', 'pgfplots_library') NOT NULL,
    description TEXT,
    documentation_url VARCHAR(500),
    usage_count INT DEFAULT 0,
    status ENUM('active', 'deprecated', 'testing') DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for performance
    INDEX idx_packages_search (package_name, package_type, status),
    INDEX idx_packages_type (package_type),
    INDEX idx_packages_status (status),
    INDEX idx_packages_usage (usage_count DESC),
    INDEX idx_packages_created (created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 2. PACKAGE REQUESTS TABLE  
-- =====================================================

CREATE TABLE IF NOT EXISTS package_requests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_name VARCHAR(100) NOT NULL,
    package_type ENUM('latex_package', 'tikz_library', 'pgfplots_library') NOT NULL,
    description TEXT NOT NULL,
    documentation_url VARCHAR(500),
    justification TEXT NOT NULL,
    use_case_example TEXT,
    
    -- Requester information
    requester_name VARCHAR(100) NOT NULL,
    requester_email VARCHAR(255) NOT NULL,
    requester_user_id INT DEFAULT NULL,
    
    -- Request metadata
    priority ENUM('low', 'medium', 'high', 'urgent') DEFAULT 'medium',
    status ENUM('pending', 'under_review', 'approved', 'rejected', 'implemented') DEFAULT 'pending',
    
    -- Admin response
    admin_notes TEXT,
    reviewed_by_email VARCHAR(255),
    reviewed_at TIMESTAMP NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Indexes for admin efficiency
    INDEX idx_requests_status (status, created_at DESC),
    INDEX idx_requests_priority (priority, status),
    INDEX idx_requests_requester (requester_email),
    INDEX idx_requests_admin (status, priority, created_at DESC),
    INDEX idx_requests_package (package_name, package_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 3. PACKAGE CHANGELOG TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS package_changelog (
    id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT,
    package_name VARCHAR(100) NOT NULL,
    action_type ENUM('added', 'updated', 'deprecated', 'removed') NOT NULL,
    old_values JSON,
    new_values JSON,
    
    -- Change metadata
    changed_by_email VARCHAR(255) NOT NULL,
    change_reason TEXT,
    request_id INT DEFAULT NULL,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Indexes for history tracking
    INDEX idx_changelog_package (package_id, created_at DESC),
    INDEX idx_changelog_timeline (created_at DESC),
    INDEX idx_changelog_admin (changed_by_email, created_at DESC),
    INDEX idx_changelog_action (action_type, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 4. ADMIN PERMISSIONS TABLE
-- =====================================================

CREATE TABLE IF NOT EXISTS admin_permissions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    permission_level ENUM('admin', 'moderator', 'reviewer') DEFAULT 'reviewer',
    granted_by VARCHAR(255),
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    INDEX idx_admin_email (email),
    INDEX idx_admin_active (is_active, permission_level)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- 5. INSERT EXISTING PACKAGES FROM SAFE_PACKAGES
-- =====================================================

-- LaTeX Packages
INSERT IGNORE INTO supported_packages (package_name, package_type, description, status) VALUES
-- Foundation packages
('fontspec', 'latex_package', 'Font selection for XeLaTeX and LuaLaTeX', 'active'),
('polyglossia', 'latex_package', 'Multilingual typesetting for XeLaTeX and LuaLaTeX', 'active'),
('xcolor', 'latex_package', 'Extended color definitions and support', 'active'),
('graphicx', 'latex_package', 'Enhanced support for graphics inclusion', 'active'),
('geometry', 'latex_package', 'Flexible page layout dimensions', 'active'),
('setspace', 'latex_package', 'Set spacing between lines', 'active'),

-- Math packages
('amsmath', 'latex_package', 'AMS mathematical facilities for LaTeX', 'active'),
('amssymb', 'latex_package', 'AMS symbol fonts', 'active'), 
('amsfonts', 'latex_package', 'AMS fonts collection', 'active'),
('mathtools', 'latex_package', 'Mathematical tools to use with amsmath', 'active'),
('physics', 'latex_package', 'Macros supporting the Mathematics of Physics', 'active'),
('siunitx', 'latex_package', 'A comprehensive SI units package', 'active'),
('cancel', 'latex_package', 'Place lines through math to show cancellation', 'active'),
('cases', 'latex_package', 'Numbered cases environment', 'active'),

-- TikZ/PGF packages  
('tikz', 'latex_package', 'Create PostScript and PDF graphics in TeX', 'active'),
('pgf', 'latex_package', 'Create PostScript and PDF graphics in TeX', 'active'),
('pgfplots', 'latex_package', 'Create normal/logarithmic plots in two and three dimensions', 'active'),

-- Additional packages
('babel', 'latex_package', 'Multilingual support for Plain TeX or LaTeX', 'active'),
('inputenc', 'latex_package', 'Accept different input encodings', 'active'),
('enumitem', 'latex_package', 'Control layout of itemize, enumerate, description', 'active'),
('hyperref', 'latex_package', 'Extensive support for hypertext in LaTeX', 'active'),
('url', 'latex_package', 'Verbatim with URL-sensitive line breaks', 'active'),
('array', 'latex_package', 'Extending the array and tabular environments', 'active'),
('booktabs', 'latex_package', 'Professional quality tables', 'active'),
('longtable', 'latex_package', 'Allow tables to flow over page boundaries', 'active'),
('multirow', 'latex_package', 'Create tabular cells spanning multiple rows', 'active'),
('caption', 'latex_package', 'Customising captions in floating environments', 'active'),
('subcaption', 'latex_package', 'Support for sub-captions', 'active'),
('float', 'latex_package', 'Improved interface for floating objects', 'active'),
('wrapfig', 'latex_package', 'Produces figures which text can flow around', 'active'),
('fancyhdr', 'latex_package', 'Extensive control of page headers and footers', 'active'),
('titlesec', 'latex_package', 'Select alternative section titles', 'active'),
('tocloft', 'latex_package', 'Control table of contents, figures, etc.', 'active'),
('parskip', 'latex_package', 'Layout with zero \\parindent, non-zero \\parskip', 'active'),
('microtype', 'latex_package', 'Subliminal refinements towards typographical perfection', 'active'),
('textcomp', 'latex_package', 'LaTeX support for the Text Companion fonts', 'active'),
('lmodern', 'latex_package', 'Latin modern fonts in outline formats', 'active'),
('csquotes', 'latex_package', 'Context sensitive quotation facilities', 'active'),
('etoolbox', 'latex_package', 'Tool-box for LaTeX programmers using e-TeX', 'active'),
('xparse', 'latex_package', 'A generic document command parser', 'active'),
('calc', 'latex_package', 'Simple arithmetic in LaTeX commands', 'active'),
('ifthen', 'latex_package', 'Conditional commands in LaTeX documents', 'active'),
('xifthen', 'latex_package', 'Extended conditional commands', 'active'),
('foreach', 'latex_package', 'Provides \\foreach command', 'active'),
('rotating', 'latex_package', 'Rotation tools, including rotated full-page floats', 'active'),
('pdflscape', 'latex_package', 'Make landscape pages display as landscape', 'active'),
('afterpage', 'latex_package', 'Execute command after the next page break', 'active'),
('changepage', 'latex_package', 'Margin adjustment and detection of odd/even pages', 'active'),
('layouts', 'latex_package', 'Display various elements of a document\'s layout', 'active'),
('lipsum', 'latex_package', 'Easy access to the Lorem Ipsum dummy text', 'active'),
('blindtext', 'latex_package', 'Producing \'blind\' text for testing', 'active');

-- TikZ Libraries  
INSERT IGNORE INTO supported_packages (package_name, package_type, description, status) VALUES
('calc', 'tikz_library', 'Coordinate calculation library for TikZ', 'active'),
('math', 'tikz_library', 'Mathematical functions and operations', 'active'),
('positioning', 'tikz_library', 'Advanced node positioning', 'active'),
('arrows.meta', 'tikz_library', 'Meta arrows for flexible arrow tips', 'active'),
('intersections', 'tikz_library', 'Calculate intersections of paths', 'active'),
('angles', 'tikz_library', 'Draw and label angles', 'active'),
('quotes', 'tikz_library', 'Quoting and labeling of angles and nodes', 'active'),
('decorations.markings', 'tikz_library', 'Add markings along paths', 'active'),
('decorations.pathreplacing', 'tikz_library', 'Path replacement decorations', 'active'),
('decorations.text', 'tikz_library', 'Text along path decorations', 'active'),
('patterns', 'tikz_library', 'Pattern fills for areas', 'active'),
('patterns.meta', 'tikz_library', 'Meta patterns with customization', 'active'),
('shadings', 'tikz_library', 'Shading effects and gradients', 'active'),
('hobby', 'tikz_library', 'Smooth curves through specified points', 'active'),
('spy', 'tikz_library', 'Magnification of parts of pictures', 'active'),
('backgrounds', 'tikz_library', 'Background layers and effects', 'active'),
('shapes.geometric', 'tikz_library', 'Geometric node shapes', 'active'),
('shapes.symbols', 'tikz_library', 'Symbol node shapes', 'active'),
('shapes.arrows', 'tikz_library', 'Arrow node shapes', 'active'),
('shapes.multipart', 'tikz_library', 'Multi-part node shapes', 'active'),
('fit', 'tikz_library', 'Fitting node around other nodes', 'active'),
('matrix', 'tikz_library', 'Matrix of nodes layout', 'active'),
('chains', 'tikz_library', 'Chain of nodes and connections', 'active'),
('automata', 'tikz_library', 'Drawing finite state automata', 'active'),
('petri', 'tikz_library', 'Petri net diagrams', 'active'),
('mindmap', 'tikz_library', 'Mind map diagrams', 'active'),
('trees', 'tikz_library', 'Tree structures and layouts', 'active'),
('datavisualization', 'tikz_library', 'Data visualization framework', 'active'),
('datavisualization.formats.functions', 'tikz_library', 'Function plotting for data visualization', 'active'),
('datavisualization.formats.files.csv', 'tikz_library', 'CSV file input for data visualization', 'active'),
('datavisualization.formats.files.json', 'tikz_library', 'JSON file input for data visualization', 'active');

-- PGFPlots Libraries
INSERT IGNORE INTO supported_packages (package_name, package_type, description, status) VALUES
('polar', 'pgfplots_library', 'Polar coordinate plots', 'active'),
('statistics', 'pgfplots_library', 'Statistical plots and functions', 'active'),
('dateplot', 'pgfplots_library', 'Date and time axis formatting', 'active'),
('fillbetween', 'pgfplots_library', 'Fill areas between curves', 'active'),
('colorbrewer', 'pgfplots_library', 'ColorBrewer color schemes', 'active'),
('groupplots', 'pgfplots_library', 'Multiple plots in a single figure', 'active'),
('ternary', 'pgfplots_library', 'Ternary diagrams and plots', 'active'),
('smithchart', 'pgfplots_library', 'Smith chart plots', 'active'),
('units', 'pgfplots_library', 'Unit handling in plots', 'active');

-- =====================================================
-- 6. GRANT ADMIN PERMISSIONS
-- =====================================================

INSERT IGNORE INTO admin_permissions (email, permission_level, granted_by) VALUES
('quochiep0504@gmail.com', 'admin', 'system');
