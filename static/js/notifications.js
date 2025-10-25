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
        this.toggleViewBtn = document.getElementById('toggleViewBtn');
        
        this.isOpen = false;
        this.pollInterval = null;
        this.currentNotifications = [];
        this.blurOverlay = null;
        this.showOnlyUnread = true; // Default: chỉ hiển thị unread
        
        if (this.bell) {
            this.init();
        }
    }
    
    init() {
        // Toggle dropdown on bell click
        this.bell.addEventListener('click', (e) => {
            e.preventDefault();
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

        // Toggle view (unread only / all)
        if (this.toggleViewBtn) {
            this.toggleViewBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                this.toggleView();
            });
        }

        // Close dropdown when clicking outside (with delay to prevent immediate close)
        document.addEventListener('click', (e) => {
            if (this.isOpen && this.dropdown && !this.dropdown.contains(e.target) && !this.bell.contains(e.target)) {
                // Small delay to prevent immediate close after opening
                setTimeout(() => {
                    if (this.isOpen) {
                        this.closeDropdown();
                    }
                }, 10);
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
            // Create and show blur overlay
            this.createBlurOverlay();
            
            // Move dropdown to body to escape all stacking contexts
            if (this.dropdown.parentElement !== document.body) {
                document.body.appendChild(this.dropdown);
            }
            
            // Position dropdown relative to bell icon
            this.positionDropdown();
            
            // Reset any forced styles and add 'open' class
            this.dropdown.style.display = '';
            this.dropdown.style.visibility = '';
            this.dropdown.style.opacity = '';
            this.dropdown.classList.add('open');
        } else {
            console.error('[Notifications] Dropdown element not found!');
        }
        this.loadNotifications();
    }
    
    applyEnhancedStyling() {
        if (!this.dropdown) return;
        
        // Apply styles to all notification items
        const items = this.dropdown.querySelectorAll('.notification-item');
        items.forEach((item, index) => {
            // Enhanced item styling
            item.style.borderBottom = '1px solid #e5e7eb';
            item.style.transition = 'all 0.2s ease';
            item.style.position = 'relative';
            
            // Force border-radius for first and last items
            if (index === 0) {
                // First item - rounded top corners
                item.style.borderTopLeftRadius = '10px';
                item.style.borderTopRightRadius = '10px';
            }
            if (index === items.length - 1) {
                // Last item - rounded bottom corners, no border
                item.style.borderBottomLeftRadius = '10px';
                item.style.borderBottomRightRadius = '10px';
                item.style.borderBottom = 'none';
            }
            
            // Add hover effects
            item.addEventListener('mouseenter', () => {
                item.style.background = '#f8fafc';
                item.style.borderLeft = '3px solid #1976d2';
                item.style.paddingLeft = '13px';
                item.style.transform = 'translateX(2px)';
            });
            
            item.addEventListener('mouseleave', () => {
                if (item.classList.contains('unread')) {
                    item.style.background = '#f0f7ff';
                    item.style.borderLeft = '3px solid #3b82f6';
                    item.style.paddingLeft = '13px';
                    item.style.opacity = '1';
                } else {
                    // Read notifications - restore subtle styling
                    item.style.background = '#fafafa';
                    item.style.borderLeft = '';
                    item.style.paddingLeft = '16px';
                    item.style.opacity = '0.7';
                }
                item.style.transform = '';
            });
            
            // Apply unread/read styling
            if (item.classList.contains('unread')) {
                item.style.background = '#f0f7ff';
                item.style.borderLeft = '3px solid #3b82f6';
                item.style.paddingLeft = '13px';
                item.style.opacity = '1';
            } else {
                // Read notifications - subtle styling
                item.style.background = '#fafafa';
                item.style.opacity = '0.7';
                item.style.borderLeft = '';
                item.style.paddingLeft = '16px';
            }
            
            // Smaller font sizes
            const textElement = item.querySelector('.notification-text');
            if (textElement) {
                textElement.style.fontSize = '13px';
                textElement.style.color = '#374151';
            }
            
            const previewElement = item.querySelector('.notification-preview');
            if (previewElement) {
                previewElement.style.fontSize = '12px';
                previewElement.style.color = '#6b7280';
                previewElement.style.fontStyle = 'italic';
            }
            
            const timeElement = item.querySelector('.notification-time');
            if (timeElement) {
                timeElement.style.fontSize = '11px';
                timeElement.style.color = '#9ca3af';
            }
        });
    }
    
    positionDropdown() {
        if (!this.bell || !this.dropdown) return;
        
        const bellRect = this.bell.getBoundingClientRect();
        const isMobile = window.innerWidth <= 575.98; // Mobile breakpoint
        const isTablet = window.innerWidth > 575.98 && window.innerWidth <= 768; // Tablet breakpoint
        
        // Always set essential positioning properties
        this.dropdown.style.position = 'fixed';
        this.dropdown.style.zIndex = '2147483647'; // Maximum z-index
        this.dropdown.style.isolation = 'isolate';
        this.dropdown.style.transform = 'translateZ(0)';
        
        if (isMobile) {
            // Mobile: Apply full-width positioning with 6px margins
            // Mobile styles: Full width with 6px margins from screen edges
            this.dropdown.style.width = `calc(100vw - 12px)`;
            this.dropdown.style.left = '6px';
            this.dropdown.style.right = '6px';
            this.dropdown.style.maxWidth = 'none';
            this.dropdown.style.minWidth = 'unset';
            this.dropdown.style.top = `${bellRect.bottom + 8}px`;
            this.dropdown.style.bottom = 'auto';
            this.dropdown.style.transform = 'translateX(0)';
            this.dropdown.style.marginLeft = '0';
            this.dropdown.style.marginRight = '0';
        } else if (isTablet) {
            // Tablet: Apply centered positioning with JavaScript (cache-proof)
            // Tablet styles: Responsive width with perfect centering
            this.dropdown.style.width = `calc(100vw - 32px)`;
            this.dropdown.style.maxWidth = '360px';
            this.dropdown.style.left = '50%';
            this.dropdown.style.right = 'auto';
            this.dropdown.style.transform = 'translateX(-50%) translateZ(0)';
            this.dropdown.style.top = `${bellRect.bottom + 8}px`;
            this.dropdown.style.bottom = 'auto';
            this.dropdown.style.marginLeft = '0';
            this.dropdown.style.marginRight = '0';
        } else {
            // Desktop: Position dropdown below bell icon, aligned to right
            const top = bellRect.bottom + 8;
            const right = window.innerWidth - bellRect.right;
            
            this.dropdown.style.top = `${top}px`;
            this.dropdown.style.right = `${right}px`;
            this.dropdown.style.left = 'auto';
            this.dropdown.style.bottom = 'auto';
            this.dropdown.style.width = ''; // Let CSS handle width
            this.dropdown.style.maxWidth = '';
            this.dropdown.style.transform = 'translateZ(0)'; // Reset transform
        }
        
        // Force solid background and enhanced styling
        this.dropdown.style.backgroundColor = 'rgb(248, 249, 250)';
        this.dropdown.style.backdropFilter = 'none';
        this.dropdown.style.borderRadius = '12px';
        this.dropdown.style.border = '2px solid rgb(59, 130, 246, 0.3)';
        this.dropdown.style.boxShadow = '0 8px 32px rgb(31 38 135 / 15%), 0 2px 8px rgb(0 0 0 / 10%)';
        this.dropdown.style.overflow = 'hidden'; // Force hide overflow to respect border-radius
        
    }

    
    closeDropdown() {
        this.isOpen = false;
        if (this.dropdown) {
            // Hide blur overlay
            this.hideBlurOverlay();
            
            // Remove 'open' class to trigger CSS transition
            this.dropdown.classList.remove('open');
            
            // Force hide if CSS transition fails
            setTimeout(() => {
                if (!this.isOpen) {
                    this.dropdown.style.display = 'none';
                    this.dropdown.style.visibility = 'hidden';
                    this.dropdown.style.opacity = '0';
                }
            }, 300); // Wait for CSS transition
        }
    }
    
    createBlurOverlay() {
        
        // Remove existing overlay if any
        this.removeBlurOverlay();
        
        // Create new overlay
        this.blurOverlay = document.createElement('div');
        this.blurOverlay.className = 'tikz-app notifications-blur-overlay';
        
        // Force inline styles to ensure visibility
        this.blurOverlay.style.position = 'fixed';
        this.blurOverlay.style.inset = '0';
        this.blurOverlay.style.background = 'rgba(0, 0, 0, 0.1)';
        this.blurOverlay.style.backdropFilter = 'blur(3px)';
        this.blurOverlay.style.zIndex = '2147483646';
        this.blurOverlay.style.opacity = '0';
        this.blurOverlay.style.visibility = 'hidden';
        this.blurOverlay.style.transition = 'opacity 0.2s ease, visibility 0.2s ease';
        
        // Add click handler to close dropdown when clicking overlay
        this.blurOverlay.addEventListener('click', () => {
            this.closeDropdown();
        });
        
        // Append to body and activate
        document.body.appendChild(this.blurOverlay);
        
        // Force reflow then activate
        requestAnimationFrame(() => {
            this.blurOverlay.style.opacity = '1';
            this.blurOverlay.style.visibility = 'visible';
            this.blurOverlay.classList.add('active');
        });
    }
    
    hideBlurOverlay() {
        if (this.blurOverlay) {
            this.blurOverlay.classList.remove('active');
            
            // Remove after transition
            setTimeout(() => {
                this.removeBlurOverlay();
            }, 200);
        }
    }
    
    removeBlurOverlay() {
        if (this.blurOverlay && this.blurOverlay.parentElement) {
            this.blurOverlay.parentElement.removeChild(this.blurOverlay);
            this.blurOverlay = null;
        }
    }
    
    toggleView() {
        this.showOnlyUnread = !this.showOnlyUnread;
        
        // Update button text and style
        if (this.toggleViewBtn) {
            if (this.showOnlyUnread) {
                this.toggleViewBtn.textContent = 'Xem tất cả';
                this.toggleViewBtn.style.background = 'none';
                this.toggleViewBtn.style.color = '#6b7280';
                this.toggleViewBtn.style.border = '1px solid #e5e7eb';
            } else {
                this.toggleViewBtn.textContent = 'Chỉ chưa đọc';
                this.toggleViewBtn.style.background = '#1976d2';
                this.toggleViewBtn.style.color = 'white';
                this.toggleViewBtn.style.border = '1px solid #1976d2';
            }
        }
        
        // Reload notifications with new filter
        this.loadNotifications();
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
            
            
        } catch (error) {
            console.error('[Notifications] Error updating badge:', error);
        }
    }
    
    async loadNotifications() {
        if (!this.list) return;
        
        this.list.innerHTML = '<div class="notifications-loading" style="padding: 40px 20px; text-align: center; color: #6c757d;"><i class="fas fa-spinner fa-spin"></i> Đang tải...</div>';
        
        try {
            const onlyUnreadParam = this.showOnlyUnread ? '&only_unread=true' : '';
            const response = await fetch(`/api/notifications?limit=20${onlyUnreadParam}`);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            this.currentNotifications = data.notifications || [];
            
            this.renderNotifications(this.currentNotifications);
            
            
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
        
        // Apply enhanced styling after rendering
        setTimeout(() => {
            this.applyEnhancedStyling();
        }, 100);
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
        
        // Handle message and content display for different notification types
        let messageText = messageMap[notif.notification_type] || 'đã thực hiện một hành động';
        let contentPreview = '';
        
        // Check for social cross-engagement notifications (comment type with "ảnh của" content)
        if (notif.notification_type === 'comment' && notif.content && notif.content.startsWith('ảnh của')) {
            // For social cross-engagement: "đã bình luận ảnh của [owner]"
            messageText = `đã bình luận ${notif.content}`;
            contentPreview = ''; // Don't show comment preview for social notifications
        } else if (notif.content && notif.notification_type !== 'follow') {
            // For regular notifications: show content as preview
            contentPreview = `<p class="notification-preview">"${notif.content}"</p>`;
        }
        
        return `
            <div class="notification-item ${unreadClass}" 
                 data-notification-id="${notif.id}"
                 data-action-url="${notif.action_url || ''}">
                <img src="${avatar}" 
                     alt="${notif.actor_username}" 
                     class="notification-avatar"
                     style="width: 24px; height: 24px; max-width: 24px; max-height: 24px;"
                     onerror="this.onerror=null; this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 24 24%22 fill=%22%23ccc%22%3E%3Cpath d=%22M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z%22/%3E%3C/svg%3E';">
                <div class="notification-content">
                    <p class="notification-text">
                        <strong>${notif.actor_username}</strong> ${messageText}
                    </p>
                    ${contentPreview}
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
                
                // Update badge
                this.updateBadge();
                
                // Navigate or reload notifications
                if (actionUrl) {
                    // If navigating away, no need to reload dropdown
                    window.location.href = actionUrl;
                } else {
                    // If staying on page, reload dropdown to show updated read status
                    this.loadNotifications();
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

        // Debug functionality (only when explicitly requested)
        if (window.location.search.includes('debug-notifications=true')) {
            setTimeout(() => {
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

