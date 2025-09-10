-- Add usage count field for profile verification
-- This tracks how many times a verification code has been successfully used

ALTER TABLE `user` 
ADD COLUMN `profile_verification_usage_count` INT DEFAULT 0 COMMENT 'Số lần mã xác thực đã được sử dụng thành công (max 5 lần)';

-- Create index for performance
CREATE INDEX `idx_profile_verification_usage` ON `user` (`profile_verification_usage_count`);

-- Update existing records to have 0 usage count
UPDATE `user` 
SET `profile_verification_usage_count` = 0 
WHERE `profile_verification_usage_count` IS NULL;
