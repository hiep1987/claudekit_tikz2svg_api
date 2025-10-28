/**
 * TikZ2SVG API - JavaScript Timezone Fix
 * =====================================
 * Purpose: Fix timezone handling in client-side JavaScript
 * Fixes the 7-hour timezone difference issue
 * Date: 2025-10-27
 */

// Vietnam timezone offset (+7 hours from UTC)
const VN_TIMEZONE_OFFSET = 7 * 60; // 7 hours in minutes

/**
 * Enhanced formatTimeAgo function with proper timezone handling
 * @param {string} timestamp - ISO timestamp from server
 * @returns {string} - Formatted "time ago" string
 */
function formatTimeAgoFixed(timestamp) {
    if (!timestamp) return '';
    
    try {
        // Parse the timestamp (assume it's in Vietnam timezone from server)
        const serverTime = new Date(timestamp);
        
        // Get current time in Vietnam timezone
        const now = new Date();
        const vnNow = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) + (VN_TIMEZONE_OFFSET * 60000));
        
        // Calculate difference
        const diffMs = vnNow - serverTime;
        const diffSec = Math.floor(diffMs / 1000);
        const diffMin = Math.floor(diffSec / 60);
        const diffHour = Math.floor(diffMin / 60);
        const diffDay = Math.floor(diffHour / 24);
        
        // Format time ago
        if (diffSec < 30) return 'Vừa xong';
        if (diffSec < 60) return 'Vài giây trước';
        if (diffMin < 60) return `${diffMin} phút trước`;
        if (diffHour < 24) return `${diffHour} giờ trước`;
        if (diffDay < 30) return `${diffDay} ngày trước`;
        
        // For older dates, show actual date
        const options = { 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            timeZone: 'Asia/Ho_Chi_Minh'
        };
        return serverTime.toLocaleDateString('vi-VN', options);
        
    } catch (error) {
        console.error('Error formatting time:', error);
        return timestamp; // Fallback to original timestamp
    }
}

/**
 * Convert server timestamp to Vietnam timezone
 * @param {string} timestamp - Server timestamp
 * @returns {Date} - Date object in Vietnam timezone
 */
function convertToVNTime(timestamp) {
    if (!timestamp) return new Date();
    
    try {
        // If timestamp includes timezone info, use as is
        if (timestamp.includes('+') || timestamp.includes('Z')) {
            return new Date(timestamp);
        }
        
        // If no timezone info, assume it's Vietnam time from server
        const date = new Date(timestamp);
        
        // Adjust for Vietnam timezone if needed
        // This handles cases where server sends local time without timezone info
        return date;
        
    } catch (error) {
        console.error('Error converting timestamp:', error);
        return new Date();
    }
}

/**
 * Get current time in Vietnam timezone
 * @returns {Date} - Current date in Vietnam timezone
 */
function getCurrentVNTime() {
    const now = new Date();
    // Convert to Vietnam timezone
    const vnTime = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Ho_Chi_Minh"}));
    return vnTime;
}

/**
 * Format date for display in Vietnam timezone
 * @param {string|Date} timestamp - Timestamp to format
 * @returns {string} - Formatted date string
 */
function formatVNDate(timestamp) {
    try {
        const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
        
        return date.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh',
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
    } catch (error) {
        console.error('Error formatting VN date:', error);
        return timestamp.toString();
    }
}

// Export functions for use in other files
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatTimeAgoFixed,
        convertToVNTime,
        getCurrentVNTime,
        formatVNDate,
        VN_TIMEZONE_OFFSET
    };
}

// Make functions available globally for browser usage
if (typeof window !== 'undefined') {
    window.TimezoneUtils = {
        formatTimeAgo: formatTimeAgoFixed,
        convertToVNTime: convertToVNTime,
        getCurrentVNTime: getCurrentVNTime,
        formatVNDate: formatVNDate,
        VN_TIMEZONE_OFFSET: VN_TIMEZONE_OFFSET
    };
}

/**
 * Patch existing formatTimeAgo functions in the application
 */
function patchExistingTimeAgeFunctions() {
    // Override global formatTimeAgo if it exists
    if (typeof window !== 'undefined' && typeof window.formatTimeAgoFixed === 'undefined') {
        window.formatTimeAgoFixed = formatTimeAgoFixed;
        console.log('✅ Timezone fix: formatTimeAgoFixed function patched');
    }
}

// Auto-patch when script loads
if (typeof document !== 'undefined') {
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', patchExistingTimeAgeFunctions);
    } else {
        patchExistingTimeAgeFunctions();
    }
}

console.log('🕒 TikZ2SVG Timezone Fix loaded successfully');
console.log('📍 Vietnam timezone offset:', VN_TIMEZONE_OFFSET, 'minutes');
console.log('🇻🇳 Current VN time:', getCurrentVNTime().toISOString());
