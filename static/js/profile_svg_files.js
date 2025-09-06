/**
 * Profile SVG Files Page JavaScript
 * IIFE to avoid global scope pollution
 */

(function() {
    'use strict';

    // ===== PRIVATE STATE =====
    let isUserActionInProgress = false;
    let activeFeedbackCount = 0;
    let deleteSvgId = null;
    let deleteCardElem = null;

    // ===== UTILITY FUNCTIONS =====
    function isTouchDevice() {
        return document.documentElement.classList.contains('is-touch');
    }

    function isLoggedIn() {
        // Use consistent appState logic from file_card.js
        return window.appState && window.appState.loggedIn === true;
    }

    function isOwner() {
        // Use consistent appState logic
        return window.appState && window.appState.isOwner === true;
    }

    function resetButtonTapState(btn) {
        btn.dataset.tapCount = '0';
        btn.classList.remove('individual-active', 'ready-to-execute');
    }

    function setButtonTapState(btn, tapCount = 1) {
        btn.dataset.tapCount = tapCount.toString();
        if (tapCount === 1) {
            btn.classList.add('individual-active', 'ready-to-execute');
        }
    }

    function autoResetButton(btn, delay = 5000) {
        setTimeout(() => {
            if (btn.dataset.tapCount === '1') {
                resetButtonTapState(btn);
            }
        }, delay);
    }

    // ===== CLIPBOARD FUNCTIONS =====
    async function copyToClipboard(text) {
        if (navigator.clipboard && window.isSecureContext) {
            try {
                await navigator.clipboard.writeText(text);
                return true;
            } catch (err) {
                console.error('Clipboard API failed:', err);
                return false;
            }
        }
        
        // Fallback
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        
        try {
            textArea.focus();
            textArea.select();
            const successful = document.execCommand('copy');
            return successful;
        } catch (err) {
            console.error('execCommand copy failed:', err);
            return false;
        } finally {
            if (document.body.contains(textArea)) {
                document.body.removeChild(textArea);
            }
        }
    }

    function updateButtonFeedback(btn, feedbackText, originalText, duration = 3000) {
        const textDiv = btn.querySelector('.text');
        if (textDiv) {
            textDiv.textContent = feedbackText;
            activeFeedbackCount++;
            
            setTimeout(() => {
                textDiv.textContent = originalText;
                activeFeedbackCount--;
            }, duration);
        }
    }

    async function copyToClipboardWithFeedback(text, btn, originalText, feedbackText, duration = 3000) {
        const success = await copyToClipboard(text);
        
        if (success) {
            updateButtonFeedback(btn, feedbackText, originalText, duration);
        } else {
            updateButtonFeedback(btn, 'Copy thất bại', originalText, duration);
            alert(`Không thể copy. Vui lòng copy thủ công: ${text}`);
        }
        
        return success;
    }

    // ===== CORE FUNCTIONS =====
    function toggleTikzCode(btn) {
        if (!isLoggedIn()) {
            showLoginModal(btn);
            return;
        }
        
        const card = btn.closest('.file-card');
        const codeBlock = card.querySelector('.tikz-code-block');
        const textDiv = btn.querySelector('.text');
        
        if (codeBlock.style.display === 'none' || !codeBlock.style.display) {
            codeBlock.style.display = 'block';
            textDiv.textContent = 'Ẩn code';
            
            setTimeout(() => {
                const textarea = codeBlock.querySelector('.tikz-cm');
                if (textarea && !textarea.CodeMirror) {
                    const existingCm = codeBlock.querySelector('.CodeMirror');
                    if (existingCm) {
                        existingCm.remove();
                    }
                    
                    const cmInstance = CodeMirror.fromTextArea(textarea, {
                        mode: 'stex',
                        theme: 'material',
                        lineNumbers: true,
                        readOnly: true,
                        lineWrapping: true,
                        foldGutter: true,
                        gutters: ['CodeMirror-linenumbers'],
                        viewportMargin: Infinity
                    });
                    
                    setTimeout(() => {
                        cmInstance.refresh();
                    }, 100);
                }
            }, 50);
        } else {
            codeBlock.style.display = 'none';
            textDiv.textContent = 'Xem Code';
        }
    }

    function copyTikzCode(btn) {
        if (!isLoggedIn()) {
            showLoginModal(btn);
            return;
        }
        
        const card = btn.closest('.file-card');
        const textarea = card.querySelector('.tikz-cm');
        
        let code = textarea.value;
        
        if (textarea.CodeMirror) {
            code = textarea.CodeMirror.getValue();
        }
        
        copyToClipboard(code).then(success => {
            if (success) {
                btn.textContent = 'Đã copy!';
                setTimeout(() => { 
                    btn.textContent = '📋 Copy'; 
                }, 2000);
            } else {
                alert('Không thể copy code. Vui lòng copy thủ công.');
            }
        });
    }

    function showDeleteModal(btn) {
        const card = btn.closest('.file-card');
        deleteCardElem = card;
        deleteSvgId = card.getAttribute('data-id');
        document.getElementById('delete-confirm-modal').style.display = 'flex';
    }

    function showLoginModal(btn) {
        const loginModal = document.getElementById('login-modal');
        if (loginModal) {
            const card = btn.closest('.file-card');
            const fileId = card ? card.getAttribute('data-id') : null;
            if (fileId) {
                loginModal.setAttribute('data-pending-file-id', fileId);
            }
            loginModal.style.display = 'flex';
        }
    }

    function hideLoginModal() {
        const loginModal = document.getElementById('login-modal');
        if (loginModal) {
            loginModal.style.display = 'none';
        }
    }

    function showLogoutModal() {
        const logoutModal = document.getElementById('logout-modal');
        if (logoutModal) {
            logoutModal.style.display = 'flex';
        }
    }

    function hideLogoutModal() {
        const logoutModal = document.getElementById('logout-modal');
        if (logoutModal) {
            logoutModal.style.display = 'none';
        }
    }

    function loginWithGoogle() {
        const currentPath = window.location.pathname + window.location.search;
        
        const pendingAction = {
            type: 'view_code',
            fileId: getCurrentPendingFileId(),
            timestamp: Date.now()
        };
        
        localStorage.setItem('tikz2svg_pending_action', JSON.stringify(pendingAction));
        
        fetch('/set_next_url?url=' + encodeURIComponent(currentPath))
            .then(() => {
                window.location.href = '/login/google';
            })
            .catch(error => {
                console.error('Error setting next URL:', error);
                window.location.href = '/login/google';
            });
    }

    function getCurrentPendingFileId() {
        const loginModal = document.getElementById('login-modal');
        if (loginModal && loginModal.style.display !== 'none') {
            const pendingFileId = loginModal.getAttribute('data-pending-file-id');
            if (pendingFileId) {
                return pendingFileId;
            }
        }
        
        const activeCard = document.querySelector('.file-card.active');
        if (activeCard) {
            return activeCard.getAttribute('data-id');
        }
        
        return null;
    }

    function executePendingAction() {
        const pendingActionStr = localStorage.getItem('tikz2svg_pending_action');
        
        if (!pendingActionStr) {
            return;
        }
        
        try {
            const pendingAction = JSON.parse(pendingActionStr);
            const now = Date.now();
            
            if (now - pendingAction.timestamp > 5 * 60 * 1000) {
                localStorage.removeItem('tikz2svg_pending_action');
                return;
            }
            
            if (pendingAction.type === 'view_code' && pendingAction.fileId) {
                const targetCard = document.querySelector(`.file-card[data-id="${pendingAction.fileId}"]`);
                
                if (targetCard) {
                    document.querySelectorAll('.file-card.active').forEach(card => {
                        card.classList.remove('active');
                    });
                    targetCard.classList.add('active');
                    
                    const viewCodeBtn = targetCard.querySelector('.view-code-btn');
                    
                    if (viewCodeBtn) {
                        targetCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        
                        setTimeout(() => {
                            viewCodeBtn.click();
                        }, 500);
                        
                        targetCard.style.animation = 'pulse 1s ease-in-out';
                        setTimeout(() => {
                            targetCard.style.animation = '';
                        }, 1000);
                    }
                }
            }
            
            localStorage.removeItem('tikz2svg_pending_action');
            
        } catch (error) {
            localStorage.removeItem('tikz2svg_pending_action');
        }
    }

    function followUser(userId) {
        isUserActionInProgress = true;
        
        fetch(`/follow/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const followBtn = document.querySelector(`.follow-btn[data-user-id="${userId}"]`);
                if (followBtn) {
                    followBtn.textContent = '👥 Bỏ theo dõi';
                    followBtn.className = 'btn btn-secondary follow-btn';
                }
                
                let followerCountElement = null;
                const spans = document.querySelectorAll('.public-profile-header span');
                for (let span of spans) {
                    if (span.textContent.includes('👥')) {
                        followerCountElement = span;
                        break;
                    }
                }
                
                if (followerCountElement) {
                    const currentText = followerCountElement.textContent;
                    const currentCount = parseInt(currentText.match(/\d+/)[0]) || 0;
                    followerCountElement.textContent = `👥 ${currentCount + 1} followers`;
                }
                
                setTimeout(() => {
                    isUserActionInProgress = false;
                }, 3000);
            } else {
                alert(data.message || 'Lỗi khi theo dõi user!');
                isUserActionInProgress = false;
            }
        })
        .catch(error => {
            console.error('Follow error:', error);
            alert('Lỗi khi theo dõi user!');
            isUserActionInProgress = false;
        });
    }

    function unfollowUser(userId) {
        isUserActionInProgress = true;
        
        fetch(`/unfollow/${userId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const unfollowBtn = document.querySelector(`.follow-btn[data-user-id="${userId}"]`);
                if (unfollowBtn) {
                    unfollowBtn.textContent = '👥 Theo dõi';
                    unfollowBtn.className = 'btn btn-primary follow-btn';
                }
                
                let followerCountElement = null;
                const spans = document.querySelectorAll('.public-profile-header span');
                for (let span of spans) {
                    if (span.textContent.includes('👥')) {
                        followerCountElement = span;
                        break;
                    }
                }
                
                if (followerCountElement) {
                    const currentText = followerCountElement.textContent;
                    const currentCount = parseInt(currentText.match(/\d+/)[0]) || 0;
                    followerCountElement.textContent = `👥 ${Math.max(0, currentCount - 1)} followers`;
                }
                
                setTimeout(() => {
                    isUserActionInProgress = false;
                }, 3000);
            } else {
                alert(data.message || 'Lỗi khi bỏ theo dõi user!');
                isUserActionInProgress = false;
            }
        })
        .catch(error => {
            console.error('Unfollow error:', error);
            alert('Lỗi khi bỏ theo dõi user!');
            isUserActionInProgress = false;
        });
    }

    // ===== TOUCH EVENT HANDLERS (2-tap logic) =====
    function handleTouchTapLogic(btn, card, currentTapCount) {
        if (currentTapCount === 0) {
            resetOtherButtons(card, btn);
            setButtonTapState(btn, 1);
            autoResetButton(btn);
            return false;
        } else if (currentTapCount === 1) {
            return true;
        }
        return false;
    }

    function resetOtherButtons(card, excludeBtn) {
        card.querySelectorAll('.Btn').forEach(otherBtn => {
            if (otherBtn !== excludeBtn) {
                resetButtonTapState(otherBtn);
            }
        });
    }

    function handleButtonAction(btn, actionType) {
        switch (actionType) {
            case 'download':
                const filename = btn.getAttribute('data-filename');
                if (filename) {
                    window.location.href = `/view_svg/${filename}`;
                }
                break;
                
            case 'facebook-share':
                const shareFilename = btn.getAttribute('data-filename');
                if (shareFilename) {
                    const shareUrl = `${window.location.origin}/view_svg/${shareFilename}`;
                    copyToClipboardWithFeedback(shareUrl, btn, 'Facebook', 'Đã copy!', 2000);
                }
                break;
                
            case 'copy-link':
                const url = btn.getAttribute('data-url');
                if (url) {
                    copyToClipboardWithFeedback(url, btn, 'Copy Link', 'Đã copy!', 2000);
                }
                break;
                
            case 'view-code':
                if (!isLoggedIn()) {
                    showLoginModal(btn);
                } else {
                    toggleTikzCode(btn);
                }
                break;
                
            case 'delete':
                showDeleteModal(btn);
                break;
                
            case 'copy-tikz':
                copyTikzCode(btn);
                break;
        }
    }

    function getButtonActionType(btn) {
        if (btn.classList.contains('download-btn')) return 'download';
        if (btn.classList.contains('fb-share-btn')) return 'facebook-share';
        if (btn.classList.contains('file-copy-link-btn')) return 'copy-link';
        if (btn.classList.contains('view-code-btn')) return 'view-code';
        if (btn.classList.contains('delete-btn')) return 'delete';
        if (btn.classList.contains('copy-tikz-btn')) return 'copy-tikz';
        return null;
    }

    function initializeTouchEvents() {
        if (!isTouchDevice()) return;

        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.Btn');
            if (!btn) return;
            
            const card = btn.closest('.file-card');
            if (!card || !card.classList.contains('active')) return;

            if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
            const currentTapCount = parseInt(btn.dataset.tapCount);
            
            if (!handleTouchTapLogic(btn, card, currentTapCount)) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
            
            const actionType = getButtonActionType(btn);
            if (actionType) {
                handleButtonAction(btn, actionType);
                
                setTimeout(() => {
                    resetButtonTapState(btn);
                }, actionType === 'download' ? 0 : 1000);
            }
            
            e.preventDefault();
            e.stopPropagation();
            return false;
        }, true);
    }

    function initializeTouchEventsForNonLoggedIn() {
        if (!isTouchDevice() || isLoggedIn()) return;

        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.Btn');
            if (!btn) return;
            
            const card = btn.closest('.file-card');
            if (!card) return;

            if (!card.classList.contains('active')) {
                document.querySelectorAll('.file-card.active').forEach(other => {
                    if (other !== card) other.classList.remove('active');
                });
                card.classList.add('active');
                return;
            }
            
            if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
            const currentTapCount = parseInt(btn.dataset.tapCount);
            
            if (!handleTouchTapLogic(btn, card, currentTapCount)) {
                e.preventDefault();
                e.stopPropagation();
                return false;
            }
            
            const actionType = getButtonActionType(btn);
            if (actionType && ['download', 'facebook-share', 'copy-link'].includes(actionType)) {
                handleButtonAction(btn, actionType);
                
                setTimeout(() => {
                    resetButtonTapState(btn);
                }, actionType === 'download' ? 0 : 2000);
            } else if (actionType) {
                showLoginModal(btn);
                setTimeout(() => {
                    resetButtonTapState(btn);
                }, 1000);
            }
            
            e.preventDefault();
            e.stopPropagation();
            return false;
        }, true);
    }

    // ===== BUTTON EVENT LISTENERS =====
    function initializeButtonEventListeners() {
        // Download button (desktop only)
        if (!isTouchDevice()) {
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.download-btn');
                if (btn) {
                    const filename = btn.getAttribute('data-filename');
                    if (filename) {
                        window.location.href = `/view_svg/${filename}`;
                    }
                }
            });
        }
        
        // View Code button (desktop only)
        if (!isTouchDevice()) {
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.view-code-btn');
                if (btn) {
                    toggleTikzCode(btn);
                }
            });
        }
        
        // Delete button (desktop only)
        if (!isTouchDevice()) {
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.delete-btn');
                if (btn) {
                    showDeleteModal(btn);
                }
            });
        }
        
        // Copy TikZ Code button (desktop only)
        if (!isTouchDevice()) {
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.copy-tikz-btn');
                if (btn) {
                    copyTikzCode(btn);
                }
            });
        }
        
        // Cancel Logout button
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.cancel-logout-btn');
            if (btn) {
                hideLogoutModal();
            }
        });
        
        // Modal Login button
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.modal-login-btn');
            if (btn) {
                loginWithGoogle();
            }
        });
        
        // Cancel Login button
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.cancel-login-btn');
            if (btn) {
                hideLoginModal();
            }
        });

        // Follow/Unfollow button handling
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('.follow-btn');
            if (!btn) return;
            const userId = btn.getAttribute('data-user-id');
            if (!userId) return;
            const isUnfollow = btn.textContent.includes('Bỏ theo dõi') || btn.classList.contains('btn-secondary');
            if (isUnfollow) {
                unfollowUser(userId);
            } else {
                followUser(userId);
            }
        });

        // Action toggle button
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('.action-toggle-btn');
            if (btn) {
                const card = btn.closest('.file-card');
                if (card) {
                    document.querySelectorAll('.file-card.active').forEach(other => {
                        if (other !== card) other.classList.remove('active');
                    });
                    card.classList.toggle('active');
                }
            }
        });

        // Close menu when clicking outside
        document.addEventListener('click', function (e) {
            const activeCard = document.querySelector('.file-card.active');
            if (activeCard) {
                if (activeCard.dataset.preventClose === 'true') {
                    return;
                }
                
                if (!activeCard.contains(e.target) && !e.target.closest('.Btn') && !e.target.closest('.action-toggle-btn')) {
                    activeCard.classList.remove('active');
                }
            }
        });

        // Delete modal event listeners
        const confirmDeleteBtn = document.getElementById('confirm-delete-btn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', function() {
            if (deleteSvgId && deleteCardElem) {
                fetch('/delete_svg', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        svg_image_id: deleteSvgId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        deleteCardElem.remove();
                        document.getElementById('delete-confirm-modal').style.display = 'none';
                        deleteSvgId = null;
                        deleteCardElem = null;
                        alert('Đã xóa ảnh thành công!');
                    } else {
                        alert(data.message || 'Có lỗi xảy ra khi xóa ảnh!');
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Có lỗi kết nối khi xóa ảnh!');
                });
            }
        });
        }

        const cancelDeleteBtn = document.getElementById('cancel-delete-btn');
        if (cancelDeleteBtn) {
            cancelDeleteBtn.addEventListener('click', function() {
                const deleteModal = document.getElementById('delete-confirm-modal');
                if (deleteModal) {
                    deleteModal.style.display = 'none';
                    deleteSvgId = null;
                    deleteCardElem = null;
                }
            });
        }

        const deleteModal = document.getElementById('delete-confirm-modal');
        if (deleteModal) {
            deleteModal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.style.display = 'none';
                    deleteSvgId = null;
                    deleteCardElem = null;
                }
            });
        }

        // Logout button logic
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function (e) {
                e.preventDefault();
                showLogoutModal();
            });
        }

        // Google login button logic
        const modalLoginBtn = document.getElementById('modal-login-btn');
        if (modalLoginBtn) {
            modalLoginBtn.addEventListener('click', function (e) {
                e.preventDefault();
                loginWithGoogle();
            });
        }

        // Mobile Menu Toggle
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        const closeMenu = document.getElementById('close-menu');
        
        if (menuToggle && mobileMenu && closeMenu) {
            menuToggle.addEventListener('click', () => mobileMenu.classList.remove('hidden'));
            closeMenu.addEventListener('click', () => mobileMenu.classList.add('hidden'));
            mobileMenu.addEventListener('click', e => {
                if(e.target === mobileMenu) mobileMenu.classList.add('hidden');
            });
        }

        // Login modal click outside to close
        const loginModal = document.getElementById('login-modal');
        if (loginModal) {
            loginModal.addEventListener('click', function(e) {
                if (e.target === this) {
                    this.style.display = 'none';
                }
            });
        }

        // Facebook share and copy link buttons (desktop only)
        if (!isTouchDevice()) {
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.fb-share-btn');
                if (btn) {
                    const filename = btn.getAttribute('data-filename');
                    if (filename) {
                        const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                        copyToClipboardWithFeedback(shareUrl, btn, 'Facebook', 'Đã copy!', 2000);
                    }
                }
            });

            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.file-copy-link-btn');
                if (btn) {
                    const url = btn.getAttribute('data-url');
                    if (url) {
                        copyToClipboardWithFeedback(url, btn, 'Copy Link', 'Đã copy!', 2000);
                    }
                }
            });
        }

        // NOTE: Like buttons are handled by file_card.js FileCardComponent.init()
        // This file focuses on profile-specific functionality
    }

    // ===== INITIALIZATION =====
    function initializeProfileSvgFiles() {
        console.log('🚀 Initializing Profile SVG Files page');
        
        if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
            document.documentElement.classList.add('is-touch');
        }
        
        // Initialize FileCard component for like buttons and other file card functionality
        // Make sure this runs after file_card.js has loaded
        if (window.FileCardComponent && typeof window.FileCardComponent.init === 'function') {
            console.log('🔄 Initializing FileCardComponent from profile_svg_files.js');
            window.FileCardComponent.init();
        } else {
            console.warn('⚠️ FileCardComponent not available in profile_svg_files.js');
        }
        
        initializeButtonEventListeners();
        initializeTouchEvents();
        
        if (!isLoggedIn()) {
            initializeTouchEventsForNonLoggedIn();
        }
        
        if (isLoggedIn()) {
            setTimeout(() => {
                try {
                    executePendingAction();
                } catch (error) {
                    // Silent error handling
                }
            }, 1000);
        }
        
        console.log('✅ Profile SVG Files page initialized successfully');
    }

    // ===== EXPORT ONLY NECESSARY FUNCTIONS =====
    window.toggleTikzCode = toggleTikzCode;
    window.copyTikzCode = copyTikzCode;
    window.showDeleteModal = showDeleteModal;
    window.loginWithGoogle = loginWithGoogle;
    window.followUser = followUser;
    window.unfollowUser = unfollowUser;
    window.executePendingAction = executePendingAction;
    window.getCurrentPendingFileId = getCurrentPendingFileId;

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeProfileSvgFiles);
    } else {
        initializeProfileSvgFiles();
    }

})();
