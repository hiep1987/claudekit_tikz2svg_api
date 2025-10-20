-- Migration Script: Add caption column to svg_image table
-- Created: October 20, 2025
-- Purpose: Add image caption feature with MathJax/LaTeX support

-- =====================================================
-- Add caption column to svg_image table
-- =====================================================

-- Check if column doesn't exist before adding
-- MySQL 8.0+ supports this syntax
ALTER TABLE svg_image 
ADD COLUMN IF NOT EXISTS caption TEXT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL
COMMENT 'Image caption/description with LaTeX/MathJax support (e.g., $x^2$, $$\\alpha$$)'
AFTER keywords;

-- =====================================================
-- Verification Query
-- =====================================================
-- Run this to verify the column was added successfully:
-- DESCRIBE svg_image;

-- Expected output should include:
-- | caption | text | YES | | NULL | |

-- =====================================================
-- Optional: Add index for caption search (if needed)
-- =====================================================
-- Uncomment if you plan to do frequent full-text search on captions
-- CREATE FULLTEXT INDEX idx_caption_fulltext ON svg_image(caption);

-- =====================================================
-- Sample Update Query (for testing)
-- =====================================================
-- Update a specific image with a caption:
-- UPDATE svg_image 
-- SET caption = 'This is a mathematical diagram showing $f(x) = x^2$ and $$\\int_{0}^{1} x dx = \\frac{1}{2}$$'
-- WHERE filename = 'example_image.svg';

-- =====================================================
-- Rollback (if needed)
-- =====================================================
-- To remove the caption column (use with caution):
-- ALTER TABLE svg_image DROP COLUMN caption;

-- =====================================================
-- Migration Complete
-- =====================================================
-- Next steps:
-- 1. Update backend API (app.py) to handle caption field
-- 2. Update view_svg route to fetch and display caption
-- 3. Create API endpoint for updating captions
-- 4. Update frontend templates with MathJax support
-- 5. Add CSS styling for caption display
-- 6. Implement JavaScript for caption editing

