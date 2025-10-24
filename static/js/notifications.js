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

        // Reposition dropdown on window resize and scroll (when dropdown is moved to body)
        window.addEventListener('resize', () => {
            if (this.isOpen) {
                this.positionDropdown();
            }
        });
        
        window.addEventListener('scroll', () => {
            if (this.isOpen) {
                this.positionDropdown();
            }
        });

        // Initial load
        this.updateBadge();

        // Start polling for new notifications (every 30 seconds)
        this.startPolling();

        if (window.location.search.includes('debug-notifications=true')) {
            console.log('[Notifications] ✅ Initialized successfully');
        }
    }
    
    toggleDropdown() {
        if (this.isOpen) {
            this.closeDropdown();
        } else {
            this.openDropdown();
        }
    }
    
    openDropdown() {
        this.isOpen = true;
        if (this.dropdown) {
            // Move dropdown to body to escape all stacking contexts
            if (this.dropdown.parentElement !== document.body) {
                document.body.appendChild(this.dropdown);
            }
            
            // Position dropdown relative to bell icon
            this.positionDropdown();
            
            // Add 'open' class to trigger CSS transition
            this.dropdown.classList.add('open');
        } else {
            console.error('[Notifications] Dropdown element not found!');
        }
        this.loadNotifications();
    }
    
    positionDropdown() {
        if (!this.bell || !this.dropdown) return;
        
        const bellRect = this.bell.getBoundingClientRect();
        
        // Position dropdown below bell icon, aligned to right
        const top = bellRect.bottom + 8;
        const right = window.innerWidth - bellRect.right;
        
        // Position dropdown (clean approach without !important)
        this.dropdown.style.position = 'fixed';
        this.dropdown.style.top = `${top}px`;
        this.dropdown.style.right = `${right}px`;
        this.dropdown.style.left = 'auto';
        this.dropdown.style.bottom = 'auto';
        this.dropdown.style.zIndex = '2147483647'; // Maximum z-index
        this.dropdown.style.isolation = 'isolate';
        this.dropdown.style.transform = 'translateZ(0)';
        
    }

    
    closeDropdown() {
        this.isOpen = false;
        if (this.dropdown) {
            // Remove 'open' class to trigger CSS transition
            this.dropdown.classList.remove('open');
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
            
            if (window.location.search.includes('debug-notifications=true')) {
                console.log(`[Notifications] Badge updated: ${count} unread`);
            }
            
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
            
                if (window.location.search.includes('debug-notifications=true')) {
                console.log(`[Notifications] Loaded ${this.currentNotifications.length} notifications`);
            }
            
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
        
        // Handle avatar path
        let avatar = '/static/default-avatar.png';
        if (notif.actor_avatar) {
            // If avatar already has /static/ prefix, use as is
            if (notif.actor_avatar.startsWith('/static/')) {
                avatar = notif.actor_avatar;
            } else {
                // Otherwise, add /static/avatars/ prefix
                avatar = `/static/avatars/${notif.actor_avatar}`;
            }
        }
        
        return `
            <div class="notification-item ${unreadClass}" 
                 data-notification-id="${notif.id}"
                 data-action-url="${notif.action_url || ''}">
                <img src="${avatar}" 
                     alt="${notif.actor_username}" 
                     class="notification-avatar"
                     onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22%23ccc%22%3E%3Cpath d=%22M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z%22/%3E%3C/svg%3E';">
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
        
        // Mark as read
        try {
            const response = await fetch(`/api/notifications/${notificationId}/read`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                if (window.location.search.includes('debug-notifications=true')) {
                    console.log(`[Notifications] Marked ${notificationId} as read`);
                }
                
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
        
        try {
            const response = await fetch('/api/notifications/mark-all-read', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                if (window.location.search.includes('debug-notifications=true')) {
                    console.log(`[Notifications] Marked ${data.count} notifications as read`);
                }
                
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
        
        // Poll every 30 seconds
        this.pollInterval = setInterval(() => {
            this.updateBadge();
        }, 30000);
    }
    
    stopPolling() {
        if (this.pollInterval) {
            clearInterval(this.pollInterval);
            this.pollInterval = null;
        }
    }
    
    destroy() {
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
        if (window.location.search.includes('debug-notifications=true')) {
            console.log('[Notifications] ✅ NotificationsManager ready');
        }

        // Debug functionality (only when explicitly requested)
        if (window.location.search.includes('debug-notifications=true')) {
            setTimeout(() => {
                console.log('[Notifications] 🔧 Debug mode: Opening dropdown automatically');
                window.notificationsManager.openDropdown();
            }, 1000);
        }
    }
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (window.notificationsManager) {
        window.notificationsManager.stopPolling();
    }
});

