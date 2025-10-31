;(function() {
"use strict";

// Initialize action buttons using data-action (Desktop only)
function initializeFileCardActions() {
    // Only handle desktop clicks - mobile will be handled by touch events
    const tikzApp = document.querySelector('.tikz-app');
    if (tikzApp && tikzApp.classList.contains('mobile-device')) {
        return;
    }
    
    // Handle clicks on image container to view/download image
    document.addEventListener('click', function(e) {
        const imgContainer = e.target.closest('.file-img-container');
        if (imgContainer) {
            // Don't trigger if clicking on like button or comment count (no longer needed - buttons outside container)
            // Buttons are now outside .file-img-container, so this check is not needed anymore
            
            const filename = imgContainer.getAttribute('data-filename');
            if (filename) {
                // Track SVG file view from image click
                if (window.analytics && window.location.pathname.includes('/search')) {
                    const searchQuery = document.body.getAttribute('data-search-query');
                    window.analytics.trackUserAction('search_result_click', {
                        'query': searchQuery,
                        'filename': filename,
                        'action': 'view_svg',
                        'source': 'image_click'
                    });
                }
                
                // Track general file view from image click
                if (window.analytics) {
                    window.analytics.trackUserAction('file_view', {
                        'filename': filename,
                        'source': window.location.pathname.includes('/search') ? 'search_image' : 'browse_image'
                    });
                }
                
                window.location.href = `/view_svg/${filename}`;
            }
            return;
        }
    });
    
    // Handle all action buttons using data-action
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('.Btn[data-action]');
        if (!btn) return;
        
        e.preventDefault();
        const action = btn.dataset.action;
        
        switch (action) {
            case 'share-facebook':
                const filename = btn.getAttribute('data-filename');
                const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                
                // Track facebook share action
                if (window.analytics) {
                    window.analytics.trackUserAction('social_share', {
                        'platform': 'facebook',
                        'filename': filename,
                        'method': 'copy_link'
                    });
                }
                
                copyToClipboard(shareUrl, btn, 'Facebook', 'Đã copy!');
                break;
                
            case 'copy-link':
                const url = btn.getAttribute('data-url');
                
                // Track copy link action
                if (window.analytics) {
                    window.analytics.trackFileCopy('link', 'button');
                }
                
                copyToClipboard(url, btn, 'Copy Link', 'Đã copy!');
                break;
                
            case 'download-image':
                const downloadFilename = btn.getAttribute('data-filename');
                
                // Track SVG file view from search results
                if (window.analytics && window.location.pathname.includes('/search')) {
                    const searchQuery = document.body.getAttribute('data-search-query');
                    window.analytics.trackUserAction('search_result_click', {
                        'query': searchQuery,
                        'filename': downloadFilename,
                        'action': 'view_svg'
                    });
                }
                
                // Track general file view
                if (window.analytics) {
                    window.analytics.trackUserAction('file_view', {
                        'filename': downloadFilename,
                        'source': window.location.pathname.includes('/search') ? 'search' : 'browse'
                    });
                }
                
                window.location.href = `/view_svg/${downloadFilename}`;
                break;
                
            case 'toggle-code':
                // Kiểm tra trạng thái đăng nhập - sử dụng helper function
                if (isUserLoggedIn()) {
                    toggleTikzCode(btn);
                } else {
                    // Hiển thị modal đăng nhập cho user chưa đăng nhập
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) {
                        loginModal.style.display = 'flex';
                    } else {
                        // Fallback: redirect to login
                        window.location.href = '/login/google';
                    }
                }
                break;
                
            case 'delete-file':
                const fileId = btn.getAttribute('data-file-id');
                if (fileId && confirm('Bạn có chắc muốn xóa file này? Hành động này không thể hoàn tác!')) {
                    deleteFile(fileId, btn);
                }
                break;
        }
    });
}

// Touch events for buttons (2-tap logic)
function initializeFileCardTouchEvents() {
    // Enhanced touch detection - check multiple indicators
    const hasTouchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouchDevice = hasTouchSupport || isMobileDevice;
    
    const tikzApp = document.querySelector('.tikz-app');
    if (!tikzApp) {
        console.error('❌ .tikz-app element not found!');
        return;
    }
    
    // Add mobile-device class if not already present
    if (isTouchDevice && !tikzApp.classList.contains('mobile-device')) {
        tikzApp.classList.add('mobile-device');
    }
    
    const isMobile = tikzApp.classList.contains('mobile-device');
    
    // Log mobile detection status
    
    if (!isMobile) {
        return;
    }

    // Use capture phase to ensure this handler runs first
    document.addEventListener('click', function(e) {
        // ==== Xử lý click vào image container (mobile) ====
        const imgContainer = e.target.closest('.file-img-container');
        if (imgContainer) {
            // Don't trigger if clicking on like button or comment count (no longer needed - buttons outside container)
            // Buttons are now outside .file-img-container, so this check is not needed anymore
            
            // Don't trigger if menu is open (user might be trying to close it)
            const card = imgContainer.closest('.file-card');
            if (card && card.classList.contains('menu-open')) {
                return;
            }
            
            const filename = imgContainer.getAttribute('data-filename');
            if (filename) {
                e.preventDefault();
                e.stopPropagation();
                
                // Track SVG file view from image click (mobile)
                if (window.analytics && window.location.pathname.includes('/search')) {
                    const searchQuery = document.body.getAttribute('data-search-query');
                    window.analytics.trackUserAction('search_result_click', {
                        'query': searchQuery,
                        'filename': filename,
                        'action': 'view_svg',
                        'source': 'image_click',
                        'device': 'mobile'
                    });
                }
                
                // Track general file view from image click (mobile)
                if (window.analytics) {
                    window.analytics.trackUserAction('file_view', {
                        'filename': filename,
                        'source': window.location.pathname.includes('/search') ? 'search_image' : 'browse_image',
                        'device': 'mobile'
                    });
                }
                
                window.location.href = `/view_svg/${filename}`;
            }
            return;
        }
        
        // ==== Xử lý action-toggle-btn (nút ...) ====
        const toggle = e.target.closest('.action-toggle-btn');
        if (toggle) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            const card = toggle.closest('.file-card');
            if (card) {
                // Đóng tất cả card khác
                document.querySelectorAll('.file-card.menu-open').forEach(other => {
                    if (other !== card) other.classList.remove('menu-open');
                });
                // Toggle card hiện tại
                card.classList.toggle('menu-open');
                
                // Log toggle action
                const isMenuOpen = card.classList.contains('menu-open');
            }
            return;
        }

        // ==== Xử lý click outside để đóng menu ====
        const activeCard = document.querySelector('.file-card.menu-open');
        if (activeCard && !activeCard.contains(e.target) && !e.target.closest('.action-toggle-btn')) {
            activeCard.classList.remove('menu-open');
            return;
        }

        // ==== Xử lý các nút .Btn ====
        const btn = e.target.closest('.file-card .Btn');
        if (!btn) return;

        const card = btn.closest('.file-card');
        if (!card || !card.classList.contains('menu-open')) {
            return;
        }

        // Initialize tap count if not exists
        if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
        const currentTapCount = parseInt(btn.dataset.tapCount);

        if (currentTapCount === 0) {
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();
            
            
            // Reset other buttons in the same card
            card.querySelectorAll('.Btn').forEach(otherBtn => {
                if (otherBtn !== btn) {
                    otherBtn.classList.remove('individual-active', 'ready-to-execute');
                    otherBtn.dataset.tapCount = '0';
                }
            });
            
            // Activate current button
            btn.classList.add('individual-active', 'ready-to-execute');
            btn.dataset.tapCount = '1';
            
            
            // Auto reset after timeout
            setTimeout(() => {
                if (btn.dataset.tapCount === '1') {
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    btn.dataset.tapCount = '0';
                }
            }, 2000); // Increased to 2s for better UX
            return;
        }

        if (currentTapCount === 1) {
            // Execute based on data-action attribute
            const action = btn.dataset.action;
            
            if (!action) {
                // Fallback for buttons without data-action
                setTimeout(() => {
                    btn.dataset.tapCount = '0';
                    btn.classList.remove('individual-active', 'ready-to-execute');
                }, 1000);
                return;
            }

            // Prevent default behavior
            e.preventDefault();
            e.stopPropagation();
            e.stopImmediatePropagation();

            switch (action) {
                case 'share-facebook':
                    const filename = btn.getAttribute('data-filename');
                    const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                    
                    // Track facebook share action (mobile)
                    if (window.analytics) {
                        window.analytics.trackUserAction('social_share', {
                            'platform': 'facebook',
                            'filename': filename,
                            'method': 'copy_link',
                            'device': 'mobile'
                        });
                    }
                    
                    copyToClipboard(shareUrl, btn, 'Facebook', 'Đã copy!');
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 2000);
                    break;
                    
                case 'copy-link':
                    const url = btn.getAttribute('data-url');
                    
                    // Track copy link action (mobile)
                    if (window.analytics) {
                        window.analytics.trackFileCopy('link', 'button_mobile');
                    }
                    
                    copyToClipboard(url, btn, 'Copy Link', 'Đã copy!');
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 2000);
                    break;
                    
                case 'download-image':
                    const downloadFilename = btn.getAttribute('data-filename');
                    
                    // Track SVG file view from search results (mobile)
                    if (window.analytics && window.location.pathname.includes('/search')) {
                        const searchQuery = document.body.getAttribute('data-search-query');
                        window.analytics.trackUserAction('search_result_click', {
                            'query': searchQuery,
                            'filename': downloadFilename,
                            'action': 'view_svg',
                            'device': 'mobile'
                        });
                    }
                    
                    // Track general file view (mobile)
                    if (window.analytics) {
                        window.analytics.trackUserAction('file_view', {
                            'filename': downloadFilename,
                            'source': window.location.pathname.includes('/search') ? 'search' : 'browse',
                            'device': 'mobile'
                        });
                    }
                    
                    if (downloadFilename) window.location.href = `/view_svg/${downloadFilename}`;
                    btn.dataset.tapCount = '0';
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    break;
                    
                case 'delete-file':
                    const fileId = btn.getAttribute('data-file-id');
                    if (fileId && confirm('Bạn có chắc muốn xóa file này? Hành động này không thể hoàn tác!')) {
                        deleteFile(fileId, btn);
                    }
                    btn.dataset.tapCount = '0';
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    break;
                    
                case 'toggle-code':
                    // Kiểm tra trạng thái đăng nhập - sử dụng helper function
                    if (isUserLoggedIn()) {
                        toggleTikzCode(btn);
                    } else {
                        // Hiển thị modal đăng nhập cho user chưa đăng nhập
                        const loginModal = document.getElementById('login-modal');
                        if (loginModal) {
                            loginModal.style.display = 'flex';
                        } else {
                            // Fallback: redirect to login
                            window.location.href = '/login/google';
                        }
                    }
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 1000);
                    break;
                    
                default:
                    // Unknown action, reset after 1 second
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 1000);
                    break;
            }
        }
    }, true); // Capture phase to ensure priority
}

// Copy to clipboard function
function copyToClipboard(text, buttonElement, originalText, feedbackText) {
    const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (navigator.clipboard && isSecureContext) {
        navigator.clipboard.writeText(text).then(function() {
            const textDiv = buttonElement.querySelector('.text');
            if (textDiv) {
                textDiv.textContent = feedbackText || 'Đã copy!';
                setTimeout(() => { 
                    textDiv.textContent = originalText; 
                }, 3000);
            }
        }).catch(function(err) {
            console.error('Clipboard API failed:', err);
            fallbackCopyToClipboard(text, buttonElement, originalText, feedbackText);
        });
    } else {
        fallbackCopyToClipboard(text, buttonElement, originalText, feedbackText);
    }
}

function fallbackCopyToClipboard(text, buttonElement, originalText, feedbackText) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            const textDiv = buttonElement.querySelector('.text');
            if (textDiv) {
                textDiv.textContent = feedbackText || 'Đã copy!';
                setTimeout(() => { 
                    textDiv.textContent = originalText; 
                }, 3000);
            }
        } else {
            alert('Không thể copy link. Vui lòng copy thủ công: ' + text);
        }
    } catch (err) {
        console.error('execCommand copy error:', err);
        alert('Không thể copy link. Vui lòng copy thủ công: ' + text);
    }
    
    document.body.removeChild(textArea);
}

// Toggle TikZ code function
function toggleTikzCode(btn) {
    const card = btn.closest('.file-card');
    const codeBlock = card.querySelector('.tikz-code-block');
    const textDiv = btn.querySelector('.text');
    
    if (codeBlock.style.display === 'none' || !codeBlock.style.display) {
        codeBlock.style.display = 'block';
        textDiv.textContent = 'Ẩn code';
        
        // Initialize CodeMirror when showing the code block
        setTimeout(() => {
            const textarea = codeBlock.querySelector('.tikz-cm');
            
            if (textarea && !textarea.CodeMirror) {
                const existingCm = codeBlock.querySelector('.CodeMirror');
                if (existingCm) {
                    existingCm.remove();
                }
                
                if (typeof CodeMirror !== 'undefined') {
                    try {
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
                        
                        // Refresh CodeMirror after a short delay
                        setTimeout(() => {
                            cmInstance.refresh();
                        }, 100);
                    } catch (error) {
                        console.error('❌ Error creating CodeMirror instance:', error);
                    }
                } else {
                    console.error('❌ CodeMirror is not defined!');
                }
            }
        }, 50);
    } else {
        codeBlock.style.display = 'none';
        textDiv.textContent = 'Xem Code';
    }
}

// Copy TikZ code function
function copyTikzCode(btn) {
    const card = btn.closest('.file-card');
    const textarea = card.querySelector('.tikz-cm');
    
    // Lấy code từ CodeMirror instance nếu có, nếu không thì từ textarea gốc
    let code = textarea.value;
    
    // Ưu tiên lấy từ CodeMirror instance
    if (textarea.CodeMirror) {
        code = textarea.CodeMirror.getValue();
    }
    
    // Kiểm tra xem có phải HTTPS hoặc localhost không
    const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
    
    if (navigator.clipboard && isSecureContext) {
        navigator.clipboard.writeText(code).then(function() {
            btn.textContent = '✅ Đã copy!';
            setTimeout(() => { 
                btn.textContent = '📋 Copy'; 
            }, 2000);
        }).catch(function(err) {
            console.error('❌ Clipboard API failed:', err);
            fallbackCopyTikzCode(code, btn);
        });
    } else {
        fallbackCopyTikzCode(code, btn);
    }
}

function fallbackCopyTikzCode(code, btn) {
    const textArea = document.createElement('textarea');
    textArea.value = code;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            btn.textContent = '✅ Đã copy!';
            setTimeout(() => { 
                btn.textContent = '📋 Copy'; 
            }, 2000);
        } else {
            alert('Không thể copy code. Vui lòng copy thủ công.');
        }
    } catch (err) {
        console.error('❌ execCommand copy error:', err);
        alert('Không thể copy code. Vui lòng copy thủ công.');
    }
    
    document.body.removeChild(textArea);
}

// ===== HELPER FUNCTIONS =====

// Safe function to check login status
function isUserLoggedIn() {
    // Use window.appState that should be initialized by index.js
    return window.appState && window.appState.loggedIn === true;
}

// ===== LIKE BUTTON FUNCTIONALITY (from search_results.js) =====

// Initialize like buttons for file cards
function initializeLikeButtons() {
    // Initialize like buttons if user is logged in
    if (isUserLoggedIn()) {
        // Support multiple prefixes: heart- and followed-heart-
        const selectors = 'input[id^="heart-"], input[id^="followed-heart-"]';
        document.querySelectorAll(selectors).forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                // Extract fileId from different prefixes
                let fileId;
                if (this.id.startsWith('followed-heart-')) {
                    fileId = this.id.replace('followed-heart-', '');
                } else {
                    fileId = this.id.replace('heart-', '');
                }
                
                const isLiked = this.checked;
                const likeButton = this.closest('.like-button');
                const currentNumber = likeButton.querySelector('.like-count.one');
                const moveNumber = likeButton.querySelector('.like-count.two');
                
                // Get current count and calculate optimistic new count
                const currentCount = parseInt(currentNumber.textContent) || 0;
                const optimisticCount = isLiked ? currentCount + 1 : Math.max(0, currentCount - 1);
                
                // Instant UI feedback: show optimistic count
                moveNumber.textContent = optimisticCount;
                
                // Prevent double click
                this.disabled = true;
                
                // Send AJAX request to backend
                fetch('/like_svg', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({
                        svg_id: fileId,
                        action: isLiked ? 'like' : 'unlike'
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Update with actual server count
                        const serverCount = data.like_count;

                        // Update both displays to server count
                        currentNumber.textContent = serverCount;
                        moveNumber.textContent = serverCount;

                        // Update checkbox state based on server response
                        this.checked = data.is_liked;

                        // ✅ NEW: Refresh likes preview text to show updated user list
                        refreshLikesPreviewText(fileId);
                    } else {
                        // Revert UI if backend failed
                        this.checked = !isLiked;
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    // Revert UI on error
                    this.checked = !isLiked;
                    alert('Có lỗi kết nối!');
                })
                .finally(() => {
                    this.disabled = false;
                });
            });
        });
    }
}

// ===== DELETE FILE FUNCTIONALITY =====

// Delete file function
function deleteFile(fileId, btn) {
    const fileCard = btn.closest('.file-card');
    if (!fileCard) return;

    // Disable button to prevent double-click
    btn.disabled = true;
    const originalText = btn.querySelector('.text').textContent;
    btn.querySelector('.text').textContent = 'Đang xóa...';
    
    fetch(`/delete_svg`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
            svg_image_id: fileId
        })
    })
    .then(response => {
        if (response.ok) {
            // Animate card removal
            fileCard.style.transition = 'all 0.3s ease';
            fileCard.style.transform = 'scale(0.8)';
            fileCard.style.opacity = '0';
            
            setTimeout(() => {
                fileCard.remove();
            }, 300);
        } else {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
    })
    .catch(error => {
        console.error('❌ Error deleting file:', error);
        alert('Có lỗi xảy ra khi xóa file. Vui lòng thử lại.');
        
        // Re-enable button
        btn.disabled = false;
        btn.querySelector('.text').textContent = originalText;
    });
}

// Initialize file card component with all functionality
// ===== INITIALIZATION =====
let isFileCardInitialized = false;

function initializeFileCardComponent() {
    if (isFileCardInitialized) {
        return;
    }
    
    isFileCardInitialized = true;
    
    // Initialize like buttons if user is logged in
    initializeLikeButtons();
    
    // Initialize touch events for mobile - Enhanced detection
    const hasTouchSupport = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    const isMobileDevice = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isTouchDevice = hasTouchSupport || isMobileDevice;
    
    if (isTouchDevice) {
        document.documentElement.classList.add('is-touch');
    } else {
    }
    
    // Initialize file card functionality
    initializeFileCardActions();
    initializeFileCardTouchEvents();

    // NEW: Initialize likes modal
    initializeLikesModal();

    // NEW: Initialize likes preview text
    initializeLikesPreview();
    
    // Add login modal event listener
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.addEventListener('click', function(e) {
            if (e.target === loginModal) {
                loginModal.style.display = 'none';
            }
        });
    }
    
    // Setup cleanup event listeners
    setupCleanupEventListeners();
    
    // Start polling for like updates
    startFilesPolling();
}

// ===== FILES POLLING FUNCTIONALITY =====

let pollingInterval = null;
let activeFeedbackCount = 0;

// Real-time synchronization for likes via polling
// Only update like counts, not entire file list
function startFilesPolling() {
    
    const pollInterval = 15000; // 15 seconds
    
    pollingInterval = setInterval(function() {
        
        // Kiểm tra flag toàn cục
        if (activeFeedbackCount > 0) {
            return;
        }
        
        // Fetch updated files data to check for like count changes
        const isLoggedIn = isUserLoggedIn();
        const apiEndpoint = isLoggedIn ? '/api/files' : '/api/public/files';
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                // Xử lý response format khác nhau giữa /api/files và /api/public/files
                const files = isLoggedIn ? data : (data.files || []);
                
                // Only update like counts if there are changes
                updateLikeCounts(files);
            })
            .catch(error => {
                console.error('Error polling likes:', error);
            });
    }, pollInterval);
    
}

// Function to update only like counts without reloading entire file list
function updateLikeCounts(files) {
    files.forEach(file => {
        const fileCard = document.querySelector(`[data-file-id="${file.id}"]`);
        if (fileCard) {
            // Update like count
            const likeCountOne = fileCard.querySelector('.like-count.one');
            const likeCountTwo = fileCard.querySelector('.like-count.two');
            if (likeCountOne && likeCountTwo) {
                const oldCount = parseInt(likeCountOne.textContent) || 0;
                const newCount = file.like_count;
                
                likeCountOne.textContent = newCount;
                
                // Only update .two if it's different (avoid disrupting ongoing animations)
                if (parseInt(likeCountTwo.textContent) !== newCount) {
                    // For polling updates, show the target number
                    likeCountTwo.textContent = newCount;
                }
            }
            
            // Update like button state if user is logged in
            if (isUserLoggedIn()) {
                const likeCheckbox = fileCard.querySelector(`input[id="heart-${file.id}"]`);
                if (likeCheckbox && likeCheckbox.checked !== file.is_liked_by_current_user) {
                    likeCheckbox.checked = file.is_liked_by_current_user;
                }
            }
        }
    });
}

// Function to stop polling
function stopFilesPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
    }
}

// ===== CLEANUP FUNCTIONALITY =====

// Cleanup function for page unload
function cleanupOnPageUnload() {
    
    // Stop polling
    stopFilesPolling();
    
    // Clear any pending timeouts
    if (window.inputPreviewTimer) {
        clearTimeout(window.inputPreviewTimer);
        window.inputPreviewTimer = null;
    }
    
    if (window.typingTimeout) {
        clearTimeout(window.typingTimeout);
        window.typingTimeout = null;
    }
    
    // Clear any other intervals or timeouts if needed
    // Add more cleanup logic here as needed
    
}

// Setup cleanup event listeners
function setupCleanupEventListeners() {
    // Cleanup when user navigates away from the page
    window.addEventListener('pagehide', cleanupOnPageUnload);
    
    // Cleanup when user closes the tab/window
    window.addEventListener('beforeunload', cleanupOnPageUnload);
    
    // Cleanup when user navigates to a different page (SPA navigation)
    window.addEventListener('unload', cleanupOnPageUnload);
    
    // Cleanup when page becomes hidden (user switches tabs)
    document.addEventListener('visibilitychange', function() {
        if (document.hidden) {
            stopFilesPolling();
        } else {
            startFilesPolling();
        }
    });
    
}

// Expose module initializer
window.FileCardComponent = {
    init: initializeFileCardComponent
};

// Auto-initialize when DOM is ready if not already initialized by other scripts
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Small delay to ensure other scripts can initialize first
        setTimeout(() => {
            if (!isFileCardInitialized && window.FileCardComponent && typeof window.FileCardComponent.init === 'function') {
                window.FileCardComponent.init();
            }
        }, 100);
    });
} else {
    // DOM already loaded, initialize immediately if not already done
    setTimeout(() => {
        if (!isFileCardInitialized && window.FileCardComponent && typeof window.FileCardComponent.init === 'function') {
            window.FileCardComponent.init();
        }
    }, 100);
}

// ===== LIKES MODAL FUNCTIONALITY =====

/**
 * Initialize likes modal functionality
 * Handles click on like count to show modal with list of users who liked
 */
function initializeLikesModal() {

    // Modal functionality removed from like count - only "Xem tất cả" button opens modal now

    // Handle modal close buttons
    document.addEventListener('click', function(e) {
        if (e.target.closest('.likes-modal-close') ||
            e.target.closest('.likes-modal-overlay')) {
            closeLikesModal();
        }
    });

    // Handle ESC key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeLikesModal();
        }
    });

    // Handle load more button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.load-more-btn')) {
            const modal = e.target.closest('.likes-modal');
            const svgId = modal.id.replace('likes-modal-', '');
            const currentOffset = parseInt(modal.dataset.offset || '0');
            const limit = 20;

            loadMoreLikes(svgId, currentOffset + limit);
        }
    });

    // Handle retry button
    document.addEventListener('click', function(e) {
        if (e.target.closest('.retry-btn')) {
            const modal = e.target.closest('.likes-modal');
            const svgId = modal.id.replace('likes-modal-', '');
            fetchLikes(svgId, 0);
        }
    });
}

/**
 * Open likes modal for a specific SVG
 */
function openLikesModal(svgId) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;

    // Show modal (no need for body scroll lock since modal is contained)
    modal.classList.add('active');

    // Reset state
    modal.dataset.offset = '0';

    // Show loading state
    showModalState(modal, 'loading');

    // Fetch likes data
    fetchLikes(svgId, 0);

    // Focus management for accessibility
    const closeBtn = modal.querySelector('.likes-modal-close');
    if (closeBtn) closeBtn.focus();
}

/**
 * Close active likes modal
 */
function closeLikesModal() {
    const activeModal = document.querySelector('.likes-modal.active');
    if (!activeModal) return;

    // Close modal (no need to restore scroll position since modal is contained)
    activeModal.classList.remove('active');

    // Clear data
    const usersList = activeModal.querySelector('.likes-users-list');
    if (usersList) usersList.innerHTML = '';
}

/**
 * Fetch likes data from API
 */
function fetchLikes(svgId, offset = 0) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;

    const limit = 20;

    fetch(`/api/svg/${svgId}/likes?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                renderLikes(modal, data, offset);
            } else {
                showModalState(modal, 'error');
            }
        })
        .catch(error => {
            console.error('Error fetching likes:', error);
            showModalState(modal, 'error');
        });
}

/**
 * Load more likes (pagination)
 */
function loadMoreLikes(svgId, offset) {
    const modal = document.getElementById(`likes-modal-${svgId}`);
    if (!modal) return;

    const loadMoreBtn = modal.querySelector('.load-more-btn');
    if (loadMoreBtn) {
        loadMoreBtn.disabled = true;
        loadMoreBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Đang tải...';
    }

    const limit = 20;

    fetch(`/api/svg/${svgId}/likes?limit=${limit}&offset=${offset}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                appendLikes(modal, data, offset);
            } else {
                if (loadMoreBtn) {
                    loadMoreBtn.disabled = false;
                    loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
                }
            }
        })
        .catch(error => {
            console.error('Error loading more likes:', error);
            if (loadMoreBtn) {
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            }
        });
}

/**
 * Render likes data in modal
 */
function renderLikes(modal, data, offset) {
    // Update total count
    const countSpan = modal.querySelector('.likes-modal-count');
    if (countSpan) countSpan.textContent = data.total_likes;

    // Get users list container
    const usersList = modal.querySelector('.likes-users-list');
    if (!usersList) return;

    // Clear existing content if offset is 0
    if (offset === 0) {
        usersList.innerHTML = '';
    }

    // Render users
    if (data.users && data.users.length > 0) {
        data.users.forEach(user => {
            const userItem = createUserListItem(user);
            usersList.appendChild(userItem);
        });

        showModalState(modal, 'content');

        // Update offset
        modal.dataset.offset = data.offset + data.limit;

        // Show/hide load more button
        const loadMoreBtn = modal.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            if (data.has_more) {
                loadMoreBtn.style.display = 'block';
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
    } else if (offset === 0) {
        showModalState(modal, 'empty');
    }
}

/**
 * Append more likes to existing list (for pagination)
 */
function appendLikes(modal, data, offset) {
    const usersList = modal.querySelector('.likes-users-list');
    if (!usersList) return;

    // Append new users
    if (data.users && data.users.length > 0) {
        data.users.forEach(user => {
            const userItem = createUserListItem(user);
            usersList.appendChild(userItem);
        });

        // Update offset
        modal.dataset.offset = data.offset + data.limit;

        // Update load more button
        const loadMoreBtn = modal.querySelector('.load-more-btn');
        if (loadMoreBtn) {
            if (data.has_more) {
                loadMoreBtn.disabled = false;
                loadMoreBtn.innerHTML = '<i class="fas fa-chevron-down"></i> Xem thêm';
            } else {
                loadMoreBtn.style.display = 'none';
            }
        }
    }
}

/**
 * Create user list item HTML element
 */
function createUserListItem(user) {
    const li = document.createElement('li');
    li.className = 'likes-user-item';

    const link = document.createElement('a');
    link.href = `/profile/${user.user_id}/svg-files`;
    link.className = 'likes-user-link';

    // Avatar
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'likes-user-avatar';

    if (user.avatar) {
        const img = document.createElement('img');
        img.src = user.avatar;
        img.alt = user.username;
        img.loading = 'lazy';

        // Add error handling for broken images
        img.onerror = function() {
            console.warn(`Failed to load avatar: ${user.avatar} for user: ${user.username}`);
            // Replace with placeholder on error
            const placeholder = document.createElement('div');
            placeholder.className = 'avatar-placeholder';
            placeholder.textContent = getInitials(user.username);
            avatarDiv.innerHTML = '';
            avatarDiv.appendChild(placeholder);
        };

        img.onload = function() {
        };

        avatarDiv.appendChild(img);
    } else {
        // Create placeholder with initials
        const placeholder = document.createElement('div');
        placeholder.className = 'avatar-placeholder';
        placeholder.textContent = getInitials(user.username);
        avatarDiv.appendChild(placeholder);
    }

    // User info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'likes-user-info';

    const nameSpan = document.createElement('span');
    nameSpan.className = 'likes-user-name';
    nameSpan.textContent = user.username;

    const timeSpan = document.createElement('span');
    timeSpan.className = 'likes-user-time';
    timeSpan.textContent = formatTimeAgo(user.liked_at);

    infoDiv.appendChild(nameSpan);
    infoDiv.appendChild(timeSpan);

    link.appendChild(avatarDiv);
    link.appendChild(infoDiv);
    li.appendChild(link);

    return li;
}

/**
 * Show different modal states (loading, content, empty, error)
 */
function showModalState(modal, state) {
    const loading = modal.querySelector('.likes-loading');
    const usersList = modal.querySelector('.likes-users-list');
    const empty = modal.querySelector('.likes-empty');
    const error = modal.querySelector('.likes-error');
    const footer = modal.querySelector('.likes-modal-footer');

    // Hide all
    if (loading) loading.style.display = 'none';
    if (usersList) usersList.style.display = 'none';
    if (empty) empty.style.display = 'none';
    if (error) error.style.display = 'none';
    if (footer) footer.style.display = 'none';

    // Show active state
    switch(state) {
        case 'loading':
            if (loading) loading.style.display = 'block';
            break;
        case 'content':
            if (usersList) usersList.style.display = 'block';
            if (footer) footer.style.display = 'flex';
            break;
        case 'empty':
            if (empty) empty.style.display = 'block';
            break;
        case 'error':
            if (error) error.style.display = 'block';
            break;
    }
}

/**
 * Get initials from username for avatar placeholder
 */
function getInitials(username) {
    if (!username) return '??';
    return username.substring(0, 2).toUpperCase();
}

/**
 * Format timestamp to "time ago" format
 */
function formatTimeAgo(timestamp) {
    if (!timestamp) return '';

    const now = new Date();
    const likedAt = new Date(timestamp);
    const diffMs = now - likedAt;
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHour = Math.floor(diffMin / 60);
    const diffDay = Math.floor(diffHour / 24);

    if (diffSec < 60) return 'Vừa xong';
    if (diffMin < 60) return `${diffMin} phút trước`;
    if (diffHour < 24) return `${diffHour} giờ trước`;
    if (diffDay < 7) return `${diffDay} ngày trước`;
    if (diffDay < 30) return `${Math.floor(diffDay / 7)} tuần trước`;
    if (diffDay < 365) return `${Math.floor(diffDay / 30)} tháng trước`;
    return `${Math.floor(diffDay / 365)} năm trước`;
}

// ===== LIKES PREVIEW TEXT FUNCTIONALITY =====

/**
 * Initialize likes preview text functionality
 * Load and display preview text below like buttons automatically
 */
function initializeLikesPreview() {
    // Handle "Xem tất cả" button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.likes-view-all-btn')) {
            const previewContainer = e.target.closest('.likes-preview-text');
            const svgId = previewContainer.dataset.svgId;
            openLikesModal(svgId);
        }
    });

    // =====================================================
    // PHASE 3: LAZY LOADING WITH INTERSECTION OBSERVER
    // =====================================================
    // Only load likes preview when card is visible in viewport
    // Reduces initial API calls from 50 to ~10 (items in viewport)
    
    const observerOptions = {
        root: null, // viewport
        rootMargin: '50px', // Load slightly before entering viewport
        threshold: 0.1 // Trigger when 10% of card is visible
    };

    // Track which cards have been loaded
    const loadedCards = new Set();

    const observer = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const card = entry.target;
                const svgId = card.dataset.fileId;
                
                // Only load once per card
                if (svgId && !loadedCards.has(svgId)) {
                    console.log(`👁️ Loading likes preview for SVG ${svgId} (visible)`);
                    loadedCards.add(svgId);
                    loadLikesPreview(svgId);
                    
                    // Stop observing this card after loading
                    observer.unobserve(card);
                }
            }
        });
    }, observerOptions);

    // Observe all file cards
    const fileCards = document.querySelectorAll('.file-card[data-file-id]');
    console.log(`🔭 Observing ${fileCards.length} file cards for lazy loading`);
    fileCards.forEach(card => observer.observe(card));
}

/**
 * Load likes preview data for a specific SVG
 * With rate limit handling and exponential backoff
 */
function loadLikesPreview(svgId, retryCount = 0) {
    fetch(`/api/svg/${svgId}/likes/preview`)
        .then(response => {
            // Handle rate limit (429)
            if (response.status === 429) {
                return response.json().then(data => {
                    const retryAfter = data.retry_after || 60;
                    console.warn(`⏱️ Rate limit exceeded for SVG ${svgId}. Retry after ${retryAfter}s`);
                    
                    // Exponential backoff: retry after delay if not too many retries
                    if (retryCount < 3) {
                        const delay = Math.min(retryAfter * 1000 * Math.pow(2, retryCount), 120000);
                        console.log(`🔄 Retrying in ${delay/1000}s (attempt ${retryCount + 1}/3)`);
                        setTimeout(() => {
                            loadLikesPreview(svgId, retryCount + 1);
                        }, delay);
                    }
                    return { success: false, rate_limited: true };
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success && data.total_likes > 0) {
                renderLikesPreview(svgId, data);
            } else if (!data.rate_limited) {
                // Only log non-rate-limit errors
                console.log(`No likes to preview for SVG ${svgId}`);
            }
        })
        .catch(error => {
            console.error('Error loading likes preview:', error);
        });
}

/**
 * Render likes preview text based on data
 */
function renderLikesPreview(svgId, data) {
    const previewContainer = document.querySelector(`.likes-preview-text[data-svg-id="${svgId}"]`);
    if (!previewContainer) return;

    const contentSpan = previewContainer.querySelector('.likes-preview-content');
    if (!contentSpan) return;

    const { total_likes, preview_users, current_user_liked } = data;

    if (total_likes === 0) {
        previewContainer.style.display = 'none';
        return;
    }

    // Generate preview text
    let previewText = generateLikesPreviewText(preview_users, total_likes, current_user_liked);

    contentSpan.textContent = previewText;
    previewContainer.style.display = 'block';
}

/**
 * Generate likes preview text based on who liked
 */
function generateLikesPreviewText(users, totalLikes, currentUserLiked) {
    if (!users || users.length === 0) return '';

    let names = [];

    // Add "Bạn" if current user liked
    if (currentUserLiked) {
        names.push('Bạn');
    }

    // Add other users (filter out current user if they're in the list)
    const otherUsers = users.filter(user => !currentUserLiked || user.user_id !== getCurrentUserId());

    // Take only 1-2 other users for preview to keep it short
    const maxOtherUsers = currentUserLiked ? 1 : 2;
    const displayUsers = otherUsers.slice(0, maxOtherUsers);

    displayUsers.forEach(user => {
        names.push(user.username);
    });

    // Calculate how many users we're showing vs total
    const displayedCount = (currentUserLiked ? 1 : 0) + displayUsers.length;
    const hasMoreUsers = totalLikes > displayedCount;

    // Build text based on actual counts
    let text = '';

    if (names.length === 1) {
        if (hasMoreUsers) {
            text = `${names[0]} và những...`;
        } else {
            text = `${names[0]} thích`;
        }
    } else if (names.length === 2) {
        if (hasMoreUsers) {
            text = `${names[0]}, ${names[1]} và những...`;
        } else {
            text = `${names[0]}, ${names[1]} thích`;
        }
    } else if (names.length >= 3) {
        text = `${names[0]}, ${names[1]} và những...`;
    }

    return text;
}

/**
 * Get current user ID (helper function)
 */
function getCurrentUserId() {
    // This should be set by the backend when rendering the page
    return window.currentUserId || null;
}

/**
 * ✅ NEW: Refresh likes preview text after like/unlike action
 * Calls the preview API to get updated user list and refreshes the display
 * With rate limit handling and exponential backoff
 */
function refreshLikesPreviewText(svgId, retryCount = 0) {

    fetch(`/api/svg/${svgId}/likes/preview`)
        .then(response => {
            // Handle rate limit (429)
            if (response.status === 429) {
                return response.json().then(data => {
                    const retryAfter = data.retry_after || 60;
                    console.warn(`⏱️ Rate limit exceeded while refreshing likes preview for SVG ${svgId}. Retry after ${retryAfter}s`);
                    
                    // Exponential backoff: retry after delay if not too many retries
                    if (retryCount < 3) {
                        const delay = Math.min(retryAfter * 1000 * Math.pow(2, retryCount), 120000);
                        console.log(`🔄 Retrying refresh in ${delay/1000}s (attempt ${retryCount + 1}/3)`);
                        setTimeout(() => {
                            refreshLikesPreviewText(svgId, retryCount + 1);
                        }, delay);
                    }
                    return { success: false, rate_limited: true };
                });
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                renderLikesPreview(svgId, data);
            } else if (!data.rate_limited) {
                // Only log non-rate-limit errors
                console.error('❌ Failed to refresh likes preview:', data.message);
            }
        })
        .catch(error => {
            console.error('❌ Error refreshing likes preview:', error);
        });
}

// Expose necessary functions to global scope
window.startFilesPolling = startFilesPolling;
window.stopFilesPolling = stopFilesPolling;
window.updateLikeCounts = updateLikeCounts;
window.cleanupOnPageUnload = cleanupOnPageUnload;
window.copyTikzCode = copyTikzCode;

})();
