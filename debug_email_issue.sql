-- Kiểm tra thông tin user datahiep93@gmail.com
SELECT id, username, email, 
       profile_verification_code, 
       profile_verification_expires_at,
       profile_verification_attempts,
       pending_profile_changes
FROM user 
WHERE email = 'datahiep93@gmail.com';

-- Kiểm tra email log gần đây
SELECT recipient, template, success, error_message, sent_at
FROM email_log 
WHERE recipient = 'datahiep93@gmail.com'
ORDER BY sent_at DESC 
LIMIT 10;

-- Kiểm tra tất cả email log gần đây
SELECT recipient, template, success, error_message, sent_at
FROM email_log 
ORDER BY sent_at DESC 
LIMIT 20;

-- Kiểm tra email log cho profile verification
SELECT recipient, template, success, error_message, sent_at
FROM email_log 
WHERE template = 'profile_settings_verification'
ORDER BY sent_at DESC 
LIMIT 10;
