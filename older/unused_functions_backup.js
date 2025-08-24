/**
 * Backup của 5 functions không sử dụng từ static/js/index.js
 * Được lưu để khôi phục nếu có lỗi
 * Tạo ngày: $(date)
 */

// 1. updateRealTimePreview - Function cho view mode (không được sử dụng)
async function updateRealTimePreview(tikzCode) {
    if (!tikzCode.trim()) return;
    
    const previewImg = document.getElementById('view-svg-img');
    if (previewImg) {
        previewImg.style.opacity = '0.5';
        previewImg.alt = 'Đang cập nhật preview...';
    }
    
    try {
        const response = await fetch('/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `code=${encodeURIComponent(tikzCode)}`
        });
        
        if (response.ok) {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            // Tìm SVG trong preview-col thay vì svg-preview
            const newSvgUrl = doc.querySelector('.preview-col img')?.src;
            
            if (newSvgUrl && previewImg) {
                previewImg.src = newSvgUrl;
                previewImg.style.opacity = '1';
                previewImg.alt = 'SVG Preview (Real-time)';
                
                // Cập nhật link download và copy link cho preview mới
                const downloadBtn = document.getElementById('view-download-svg-btn');
                if (downloadBtn) {
                    downloadBtn.href = newSvgUrl;
                }
                
                // Cập nhật sự kiện copy link cho preview mới
                const copyLinkBtn = document.getElementById('view-copy-link-btn');
                if (copyLinkBtn) {
                    copyLinkBtn.onclick = function() {
                        copyToClipboard(newSvgUrl, this, '🔗 Copy Link');
                    };
                }
            }
        }
    } catch (error) {
        console.log('Preview update failed:', error);
        if (previewImg) {
            previewImg.style.opacity = '1';
            previewImg.alt = 'SVG Preview';
        }
    }
}

// 2. refreshLoginStatus - Function cập nhật trạng thái đăng nhập (không được sử dụng)
function refreshLoginStatus() {
    // Cập nhật trạng thái đăng nhập từ server
    fetch('/api/check_login_status')
        .then(response => response.json())
        .then(data => {
            const wasLoggedIn = window.isLoggedIn;
            window.isLoggedIn = data.logged_in;
            
            // Cập nhật localStorage
            localStorage.setItem('login_status', window.isLoggedIn ? 'logged_in' : 'logged_out');
            
            // Nếu trạng thái đăng nhập thay đổi, restart polling
            if (!wasLoggedIn && window.isLoggedIn) {
                console.log('🔄 User logged in, restarting polling...');
                stopFilesPolling();
                startFilesPolling();
            } else if (wasLoggedIn && !window.isLoggedIn) {
                console.log('🔄 User logged out, restarting polling...');
                stopFilesPolling();
                startFilesPolling();
            }
        })
        .catch(error => {
            console.error('Error checking login status:', error);
        });
}

// 3. startFilesPolling - Function bắt đầu polling likes (không được sử dụng)
function startFilesPolling() {
    console.log('🔄 Starting likes polling...');
    
    const pollInterval = 15000; // 15 seconds
    
    pollingInterval = setInterval(function() {
        console.log('🔄 Polling likes...', new Date().toLocaleTimeString());
        
        // Kiểm tra flag toàn cục
        if (window.activeFeedbackCount > 0) {
            return;
        }
        
        // Fetch updated files data to check for like count changes
        const apiEndpoint = window.isLoggedIn ? '/api/files' : '/api/public/files';
        fetch(apiEndpoint)
            .then(response => response.json())
            .then(data => {
                // Xử lý response format khác nhau giữa /api/files và /api/public/files
                const files = window.isLoggedIn ? data : (data.files || []);
                
                // Only update like counts if there are changes
                updateLikeCounts(files);
            })
            .catch(error => {
                console.error('Error polling likes:', error);
            });
    }, pollInterval);
    
    console.log('🔄 Started likes polling (15s interval)');
}

// 4. updateLikeCounts - Function cập nhật số like (không được sử dụng)
function updateLikeCounts(files) {
    files.forEach(file => {
        const fileCard = document.querySelector(`[data-file-id="${file.id}"]`);
        if (fileCard) {
            // Update like count
            const likeCountOne = fileCard.querySelector('.like-count.one');
            const likeCountTwo = fileCard.querySelector('.like-count.two');
            if (likeCountOne && likeCountTwo) {
                likeCountOne.textContent = file.like_count;
                likeCountTwo.textContent = file.like_count;
            }
            
            // Update like button state if user is logged in
            if (window.isLoggedIn) {
                const likeCheckbox = fileCard.querySelector(`input[id="heart-${file.id}"]`);
                if (likeCheckbox && likeCheckbox.checked !== file.is_liked_by_current_user) {
                    likeCheckbox.checked = file.is_liked_by_current_user;
                }
            }
        }
    });
}

// 5. stopFilesPolling - Function dừng polling (không được sử dụng)
function stopFilesPolling() {
    if (pollingInterval) {
        clearInterval(pollingInterval);
        pollingInterval = null;
        console.log('🔄 Stopped files polling');
    }
}

// Export để có thể sử dụng nếu cần
window.updateRealTimePreview = updateRealTimePreview;
window.refreshLoginStatus = refreshLoginStatus;
window.startFilesPolling = startFilesPolling;
window.updateLikeCounts = updateLikeCounts;
window.stopFilesPolling = stopFilesPolling;
