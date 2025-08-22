// Initialize action buttons using data-action
function initializeFileCardActions() {
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
                copyToClipboard(shareUrl, btn, 'Facebook', 'Đã copy!');
                break;
                
            case 'copy-link':
                const url = btn.getAttribute('data-url');
                copyToClipboard(url, btn, 'Copy Link', 'Đã copy!');
                break;
                
            case 'download-image':
                const downloadFilename = btn.getAttribute('data-filename');
                window.location.href = `/view_svg/${downloadFilename}`;
                break;
                
            case 'toggle-code':
                // Kiểm tra trạng thái đăng nhập - sử dụng biến từ server
                if (typeof isLoggedIn !== 'undefined' && isLoggedIn) {
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
        }
    });
}

// Touch events for buttons (2-tap logic)
function initializeFileCardTouchEvents() {
    // Detect touch environment
    const isTouch = document.documentElement.classList.contains('is-touch');
    if (!isTouch) return;

    document.addEventListener('click', function(e) {
        const toggle = e.target.closest('.action-toggle-btn');
        if (toggle) {
            const card = toggle.closest('.file-card');
            if (card) {
                document.querySelectorAll('.file-card.active').forEach(other => {
                    if (other !== card) other.classList.remove('active');
                });
                card.classList.toggle('active');
            }
            return;
        }

        const btn = e.target.closest('.file-card .Btn');
        if (!btn) return;

        const card = btn.closest('.file-card');
        if (!card || !card.classList.contains('active')) return;

        if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
        const currentTapCount = parseInt(btn.dataset.tapCount);

        if (currentTapCount === 0) {
            e.preventDefault();
            e.stopPropagation();
            // reset other buttons
            card.querySelectorAll('.Btn').forEach(otherBtn => {
                if (otherBtn !== btn) {
                    otherBtn.classList.remove('individual-active', 'ready-to-execute');
                    otherBtn.dataset.tapCount = '0';
                }
            });
            btn.classList.add('individual-active', 'ready-to-execute');
            btn.dataset.tapCount = '1';
            setTimeout(() => {
                if (btn.dataset.tapCount === '1') {
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    btn.dataset.tapCount = '0';
                }
            }, 5000);
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
            if (typeof e.stopImmediatePropagation === 'function') e.stopImmediatePropagation();

            switch (action) {
                case 'share-facebook':
                    const filename = btn.getAttribute('data-filename');
                    const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                    copyToClipboard(shareUrl, btn, 'Facebook', 'Đã copy!');
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 2000);
                    break;
                    
                case 'copy-link':
                    const url = btn.getAttribute('data-url');
                    copyToClipboard(url, btn, 'Copy Link', 'Đã copy!');
                    setTimeout(() => {
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                    }, 2000);
                    break;
                    
                case 'download-image':
                    const downloadFilename = btn.getAttribute('data-filename');
                    if (downloadFilename) window.location.href = `/view_svg/${downloadFilename}`;
                    btn.dataset.tapCount = '0';
                    btn.classList.remove('individual-active', 'ready-to-execute');
                    break;
                    
                case 'toggle-code':
                    // Kiểm tra trạng thái đăng nhập - sử dụng biến từ server
                    if (typeof isLoggedIn !== 'undefined' && isLoggedIn) {
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
    }, true);
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
        console.log('🔄 Using fallback copy method for TikZ code (no clipboard permission)');
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

// ===== LIKE BUTTON FUNCTIONALITY (from search_results.js) =====

// Initialize like buttons for file cards
function initializeLikeButtons() {
    // Initialize like buttons if user is logged in
    if (typeof isLoggedIn !== 'undefined' && isLoggedIn) {
        document.querySelectorAll('input[id^="heart-"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                const fileId = this.id.replace('heart-', '');
                const isLiked = this.checked;
                const likeButton = this.closest('.like-button');
                const currentNumber = likeButton.querySelector('.like-count.one');
                const moveNumber = likeButton.querySelector('.like-count.two');
                
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
                        // Update UI with new like count
                        const newCount = data.like_count;
                        currentNumber.textContent = newCount;
                        moveNumber.textContent = newCount;
                        
                        // Update checkbox state based on server response
                        this.checked = data.is_liked;
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

// ===== MAIN INITIALIZATION (from search_results.js) =====

// Initialize file card component with all functionality
function initializeFileCardComponent() {
    // Initialize like buttons if user is logged in
    initializeLikeButtons();
    
    // Initialize touch events for mobile
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.documentElement.classList.add('is-touch');
    }
    
    // Initialize file card functionality
    initializeFileCardActions();
    initializeFileCardTouchEvents();
    
    // Add login modal event listener
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.addEventListener('click', function(e) {
            if (e.target === loginModal) {
                loginModal.style.display = 'none';
            }
        });
    }
}

// ===== DOM READY LISTENER =====

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeFileCardComponent();
});
