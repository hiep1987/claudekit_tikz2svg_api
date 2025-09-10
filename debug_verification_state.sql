-- Debug verification state for specific user
-- Replace USER_ID with your actual user ID

SELECT 
    id,
    username,
    profile_verification_code,
    profile_verification_expires_at,
    profile_verification_usage_count,
    pending_profile_changes,
    profile_verification_attempts,
    CASE 
        WHEN profile_verification_code IS NULL THEN 'NO_CODE'
        WHEN profile_verification_expires_at < NOW() THEN 'EXPIRED'
        WHEN profile_verification_usage_count >= 5 THEN 'USAGE_LIMIT_EXCEEDED'
        WHEN profile_verification_usage_count > 0 AND profile_verification_usage_count < 5 THEN 'SHOULD_HIDE_FORM'
        ELSE 'SHOULD_SHOW_FORM'
    END as expected_form_state,
    TIMESTAMPDIFF(MINUTE, NOW(), profile_verification_expires_at) as minutes_until_expiry
FROM user 
WHERE id = 1; -- Replace with your user ID
