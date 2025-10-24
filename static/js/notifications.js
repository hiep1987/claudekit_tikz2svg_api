/**
 * NOTIFICATIONS SYSTEM - JavaScript
 * Version: 1.0.0
 * Date: 2025-10-24
 * 
 * Manages in-app notifications: badge updates, dropdown, interactions
 */

class NotificationsManager {
    constructor() {
        this.bell = document.getElementById('notificationsBell');
        this.badge = document.getElementById('notificationBadge');
        this.dropdown = document.getElementById('notificationsDropdown');
        this.list = document.getElementById('notificationsList');
        this.markAllReadBtn = document.getElementById('markAllReadBtn');
        
        this.isOpen = false;
        this.pollInterval = null;
        this.currentNotifications = [];
        
        if (this.bell) {
            this.init();
        }
    }
    
    init() {
        console.log('[Notifications] Initializing NotificationsManager');
        
        // Toggle dropdown on bell click
        this.bell.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown();
        });
        
        // Mark all as read
        if (this.markAllReadBtn) {
            this.markAllReadBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.markAllAsRead();
            });
        }
        
        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (this.isOpen && this.dropdown && !this.dropdown.contains(e.target)) {
                this.closeDropdown();
            }
        });
        
        // Initial load
        this.updateBadge();
        
        // Start polling for new notifications (every 30 seconds)
        this.startPolling();
        
        console.log('[Notifications] ✅ Initialized successfully');
    }
    
    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    openDropdown() {
        console.log('[Notifications] Opening dropdown');
        this.isOpen = true;
        if (this.dropdown) {
            this.dropdown.style.display = 'block';
        }
        this.loadNotifications();
    }
    
    closeDropdown() {
        console.log('[Notifications] Closing dropdown');
        this.isOpen = false;
        if (this.dropdown) {
            this.dropdown.style.display = 'none';
        }
    }
    
    async updateBadge() {
        try {
            const response = await fetch('/api/notifications/unread-count');
            
            if (!response.ok) {
                console.error('[Notifications] Failed to fetch unread count:', response.status);
                return;
            }
            
            const data = await response.json();
            const count = data.count || 0;
            
            if (this.badge) {
                if (count > 0) {
                    this.badge.textContent = count > 99 ? '99+' : count;
                    this.badge.style.display = 'block';
                } else {
                    this.badge.style.display = 'none';
                }
            }
            
            console.log(`[Notifications] Badge updated: ${count} unread`);
            
        } catch (error) {
            console.error('[Notifications] Error updating badge:', error);
        }
    }
    
    async loadNotifications() {
        if (!this.list) return;
        
        this.list.innerHTML = '<div class="notifications-loading" style="padding: 40px 20px; text-align: center; color: #6c757d;"><i class="fas fa-spinner fa-spin"></i> Đang tải...</div>';
        
        try {
            const response = await fetch('/api/notifications?limit=20');
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.currentNotifications = data.notifications || [];
            
            this.renderNotifications(this.currentNotifications);
            
            console.log(`[Notifications] Loaded ${this.currentNotifications.length} notifications`);
            
        } catch (error) {
            console.error('[Notifications] Error loading notifications:', error);
            this.list.innerHTML = '<div class="notifications-empty"><i class="fas fa-exclamation-triangle"></i><p>Không thể tải thông báo</p></div>';
        }
    }
    
    renderNotifications(notifications) {
        if (!notifications || notifications.length === 0) {
            this.list.innerHTML = `
                <div class="notifications-empty">
                    <i class="fas fa-bell-slash"></i>
                    <p>Chưa có thông báo nào</p>
                </div>
            `;
            return;
        }
        
        this.list.innerHTML = notifications.map(notif => this.renderNotificationItem(notif)).join('');
        
        // Add click handlers
        this.list.querySelectorAll('.notification-item').forEach(item => {
            item.addEventListener('click', (e) => {
                const notifId = parseInt(item.dataset.notificationId);
                const actionUrl = item.dataset.actionUrl;
                
                this.handleNotificationClick(notifId, actionUrl);
            });
        });
    }
    
    renderNotificationItem(notif) {
        const iconMap = {
            'like': '❤️',
            'comment': '💬',
            'reply': '↩️',
            'follow': '👤'
        };
        
        const messageMap = {
            'like': 'đã thích bức ảnh của bạn',
            'comment': 'đã bình luận vào bức ảnh của bạn',
            'reply': 'đã trả lời bình luận của bạn',
            'follow': 'đã theo dõi bạn'
        };
        
        const timeAgo = this.formatTimeAgo(notif.created_at);
        const unreadClass = notif.is_read ? '' : 'unread';
        const avatar = notif.actor_avatar || '/static/default-avatar.png';
        
        return `
            <div class="notification-item ${unreadClass}" 
                 data-notification-id="${notif.id}"
                 data-action-url="${notif.action_url || ''}">
                <img src="${avatar}" 
                     alt="${notif.actor_username}" 
                     class="notification-avatar"
                     onerror="this.src='/static/default-avatar.png'">
                <div class="notification-content">
                    <p class="notification-text">
                        <strong>${notif.actor_username}</strong> ${messageMap[notif.notification_type]}
                    </p>
                    ${notif.content ? `<p class="notification-preview">"${notif.content}"</p>` : ''}
                    <span class="notification-time">${timeAgo}</span>
                </div>
            </div>
        `;
    }
    
    async handleNotificationClick(notificationId, actionUrl) {
        console.log(`[Notifications] Clicked notification ${notificationId}`);
        
        // Mark as read
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                console.log(`[Notifications] Marked ${notificationId} as read`);
                
                // Update badge
                this.updateBadge();
                
                // Navigate
                if (actionUrl) {
                    window.location.href = actionUrl;
                }
            } else {
                console.error('[Notifications] Failed to mark as read:', response.status);
                
                // Still navigate even if mark as read fails
                if (actionUrl) {
                    window.location.href = actionUrl;
                }
            }
        } catch (error) {
            console.error('[Notifications] Error marking notification as read:', error);
            
            // Still navigate
            if (actionUrl) {
                window.location.href = actionUrl;
            }
        }
    }
    
    async markAllAsRead() {
        console.log('[Notifications] Marking all as read');
        
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                console.log(`[Notifications] Marked ${data.count} notifications as read`);
                
                // Reload notifications
                this.loadNotifications();
                
                // Update badge
                this.updateBadge();
            } else {
                console.error('[Notifications] Failed to mark all as read:', response.status);
            }
        } catch (error) {
            console.error('[Notifications] Error marking all as read:', error);
        }
    }
    
    formatTimeAgo(timestamp) {
        if (!timestamp) return '';
        
        const now = new Date();
        const past = new Date(timestamp);
        const diffMs = now - past;
        const diffMins = Math.floor(diffMs / 60000);
        
        if (diffMins < 1) return 'Vừa xong';
        if (diffMins < 60) return `${diffMins} phút trước`;
        
        const diffHours = Math.floor(diffMins / 60);
        if (diffHours < 24) return `${diffHours} giờ trước`;
        
        const diffDays = Math.floor(diffHours / 24);
        if (diffDays < 7) return `${diffDays} ngày trước`;
        
        // Format date for older notifications
        const options = { day: 'numeric', month: 'short' };
        return past.toLocaleDateString('vi-VN', options);
    }
    
    startPolling() {
        console.log('[Notifications] Starting polling (30s interval)');
        
        // Poll every 30 seconds
        this.pollInterval = setInterval(() => {
            this.updateBadge();
        }, 30000);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            console.log('[Notifications] Stopping polling');
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    destroy() {
        console.log('[Notifications] Destroying NotificationsManager');
        this.stopPolling();
        
        // Remove event listeners
        if (this.bell) {
            this.bell.replaceWith(this.bell.cloneNode(true));
        }
        if (this.markAllReadBtn) {
            this.markAllReadBtn.replaceWith(this.markAllReadBtn.cloneNode(true));
        }
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Only initialize if notifications bell exists (user is logged in)
    if (document.getElementById('notificationsBell')) {
        window.notificationsManager = new NotificationsManager();
        console.log('[Notifications] ✅ NotificationsManager ready');
    } else {
        console.log('[Notifications] Bell not found, skipping initialization (user not logged in)');
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.notificationsManager) {
        window.notificationsManager.stopPolling();
    }
});

