-- =====================================================
-- ADD CJKutf8 PACKAGE TO SUPPORTED_PACKAGES
-- =====================================================
-- Thêm gói CJKutf8 để hỗ trợ chữ CJK (Chinese, Japanese, Korean)
-- 
-- Usage trong TikZ code:
-- %!<CJKutf8>
-- 
-- \begin{CJK*}{UTF8}{gbsn}
--   富贵
-- \end{CJK*}
-- =====================================================

USE tikz2svg_local;

-- Kiểm tra xem gói đã tồn tại chưa
SELECT 
    CASE 
        WHEN COUNT(*) > 0 THEN '⚠️  Gói CJKutf8 đã tồn tại!'
        ELSE '✅ Sẵn sàng thêm CJKutf8'
    END as status
FROM supported_packages 
WHERE package_name = 'CJKutf8';

-- Thêm gói CJKutf8 vào hệ thống
INSERT INTO supported_packages (package_name, status, created_at, updated_at)
SELECT 'CJKutf8', 'manual', NOW(), NOW()
WHERE NOT EXISTS (
    SELECT 1 FROM supported_packages WHERE package_name = 'CJKutf8'
);

-- Verify kết quả
SELECT 
    package_name,
    status,
    created_at,
    CASE 
        WHEN status = 'active' THEN '🟢 Có sẵn trong template'
        WHEN status = 'manual' THEN '🟡 Cần %!<CJKutf8> trong code'
    END as usage_instruction
FROM supported_packages 
WHERE package_name = 'CJKutf8';

-- Log vào changelog
INSERT INTO package_changelog (
    package_name, 
    action_type, 
    new_values, 
    changed_by_email, 
    change_reason, 
    created_at
)
VALUES (
    'CJKutf8',
    'added',
    '{"status": "manual", "description": "Package for CJK (Chinese, Japanese, Korean) character support"}',
    'quochiep0504@gmail.com',
    'Added CJKutf8 package for Chinese character display support (富贵)',
    NOW()
);

SELECT '🎉 CJKutf8 đã được thêm vào hệ thống!' as result;
SELECT '📝 Sử dụng: %!<CJKutf8> trong TikZ code' as instruction;

