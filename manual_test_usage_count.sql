-- Manual test: Set usage_count = 1 to see if form hides
-- Replace USER_ID with your actual user ID

UPDATE user 
SET profile_verification_usage_count = 1 
WHERE id = 1; -- Replace with your user ID

-- Check the result
SELECT 
    id,
    username,
    profile_verification_code,
    profile_verification_usage_count,
    CASE 
        WHEN profile_verification_usage_count > 0 AND profile_verification_usage_count < 5 THEN 'FORM_SHOULD_BE_HIDDEN'
        ELSE 'FORM_SHOULD_BE_VISIBLE'
    END as expected_state
FROM user 
WHERE id = 1; -- Replace with your user ID
