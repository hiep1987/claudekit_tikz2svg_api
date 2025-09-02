// ===== PROFILE FOLLOWED POSTS JAVASCRIPT =====
// Tách từ templates/profile_followed_posts.html
// Version: 1.0.0
// Date: 2025-08-26

(function() {
    'use strict';
    
    // ===== FOUC PREVENTION =====
    // Prevent Flash of Unstyled Content
    document.body.classList.add('fouc-fix');
    
    // Show content when DOM is ready
    document.addEventListener('DOMContentLoaded', function() {
        document.body.classList.add('loaded');
    });
    
    // Extract server-side data from HTML attributes instead of global variables
    const serverData = document.getElementById('server-data');
    const isLoggedIn = serverData ? serverData.dataset.isLoggedIn === 'true' : false;
    const isOwner = serverData ? serverData.dataset.isOwner === 'true' : false;
    
    // Global variable to store current posts for polling comparison
    let currentPosts = [];
    let activeFeedbackCount = 0;
    
    // Polling interval references for cleanup
    let followedPostsPollingInterval = null;
    let likePollingInterval = null;

    // ===== MAIN INITIALIZATION FUNCTION =====
    function initializeApp() {
        // ==== Logout button logic ====
        const logoutBtn = document.getElementById('logout-btn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', function (e) {
                e.preventDefault();
                const logoutModal = document.getElementById('logout-modal');
                if (logoutModal) logoutModal.style.display = 'flex';
            });
        }

        // ==== Cancel logout button logic ====
        const cancelLogoutBtn = document.getElementById('cancel-logout-btn');
        if (cancelLogoutBtn) {
            cancelLogoutBtn.addEventListener('click', function (e) {
                e.preventDefault();
                const logoutModal = document.getElementById('logout-modal');
                if (logoutModal) logoutModal.style.display = 'none';
            });
        }

        // ==== Google login button logic ====
        const googleLoginBtn = document.querySelector('.google-login-btn');
        if (googleLoginBtn) {
            googleLoginBtn.addEventListener('click', function (e) {
                e.preventDefault();
                const currentPath = window.location.pathname + window.location.search;
                fetch('/set_next_url?url=' + encodeURIComponent(currentPath))
                    .then(() => window.location.href = '/login/google')
                    .catch(error => {
                        console.error('Error setting next URL:', error);
                        window.location.href = '/login/google';
                    });
            });
        }

        // ==== Load followed posts ====
        const followedSection = document.querySelector('.followed-posts-section');
        if (followedSection && followedSection.dataset.isOwner === 'true') {
            loadFollowedPosts();
            startFollowedPostsPolling();
        }

        // ==== Initialize button logic for followed posts ====
        // Touch device detection
        if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
            document.documentElement.classList.add('is-touch');
        }

        // ==== Initialize touch events for buttons ====
        initializeTouchBtnEvents();
        
        // ==== Initialize simple touch events for not logged in users ====
        if (!isLoggedIn) {
            initializeSimpleTouchEventsForNotLoggedIn();
        }

        // ==== Initialize CodeMirror ====
        if (typeof CodeMirror !== 'undefined') {
            initializeCodeMirror();
        } else {
            setTimeout(() => {
                if (typeof CodeMirror !== 'undefined') {
                    initializeCodeMirror();
                } else {
                    console.error('❌ CodeMirror failed to load');
                }
            }, 1000);
        }
        
        // ==== Initialize Facebook share buttons and copy link buttons ====
        initializeFbShareButtons();
        initializeCopyLinkButtons();
        
        // ==== Start polling for real-time updates ====
        if (isLoggedIn) {
            startLikePolling();
        }
        
        // ==== Mobile Menu Toggle ====
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
        
        // ==== Đóng menu khi click bên ngoài ====
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
        
        // ==== Event delegation for dynamic elements ====
        document.addEventListener('click', function(e) {
            // Handle download image button clicks
            const downloadBtn = e.target.closest('.download-image-btn');
            if (downloadBtn) {
                const filename = downloadBtn.getAttribute('data-filename');
                if (filename) {
                    window.location.href = `/view_svg/${filename}`;
                }
            }

            // Handle toggle code button clicks (only for non-touch devices)
            const toggleCodeBtn = e.target.closest('.toggle-code-btn');
            if (toggleCodeBtn && !document.documentElement.classList.contains('is-touch')) {
                toggleTikzCode(toggleCodeBtn);
            }

            // Handle copy TikZ code button clicks
            const copyTikzBtn = e.target.closest('.copy-tikz-btn');
            if (copyTikzBtn) {
                copyTikzCode(copyTikzBtn);
            }
        });
    }

    // ===== INITIALIZE APP WHEN SCRIPT LOADS =====
    // Script is loaded at end of body, so DOM is ready
    // Use DOMContentLoaded for faster initialization (improved FOUC prevention)
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeApp);
    } else {
        // DOM is already ready
        initializeApp();
    }

    // Load followed posts from API
    function loadFollowedPosts() {
        // // // console.log('🔄 loadFollowedPosts called...');
        const container = document.getElementById('followed-posts-container');
        // // // console.log('🔄 Container found:', !!container);
        
        // Kiểm tra flag toàn cục
        if (activeFeedbackCount > 0) {
            return;
        }
        
        fetch('/api/followed_posts')
            .then(response => {
                if (!response.ok) {
                    if (response.status === 401) {
                        // User not logged in
                        container.innerHTML = `
                            <div class="no-followed-posts">
                                <div class="no-followed-posts-icon">🔒</div>
                                <h4>Chưa đăng nhập</h4>
                                <p>Vui lòng đăng nhập để xem bài đăng từ người bạn theo dõi</p>
                            </div>
                        `;
                        return;
                    }
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(posts => {
                if (!posts) return;
                
                if (posts.length === 0) {
                    container.innerHTML = `
                        <div class="no-followed-posts">
                            <div class="no-followed-posts-icon">👥</div>
                            <h4>Chưa có bài đăng nào</h4>
                            <p>Hãy theo dõi một số người dùng để xem bài đăng của họ ở đây</p>
                        </div>
                    `;
                    return;
                }
                
                // Update global currentPosts variable for polling comparison
                currentPosts = posts;
                
                // Render posts
                const postsHTML = posts.map(post => `
                    <div class="file-card followed-post-card" data-post-id="${post.id}">
                      <button class="action-toggle-btn" type="button" aria-label="Hiện menu hành động">⋯</button>
                      <div class="file-info">
                        <div class="file-creator" style="margin-bottom: 0; font-size: 12px;">
                          👤 <a href="/profile/${post.creator_id}/svg-files" class="creator-link" data-creator-username="${post.creator_username}" data-creator-id="${post.creator_id}" style="text-decoration: none; color: #1976d2; font-weight: 700; font-size: 13px;">
                            ${post.creator_username}
                          </a>
                          <span style="margin-left:8px; color: #666; font-size: 11px;">${post.created_time_vn}</span>
                        </div>
                      </div>
                      <div class="file-img-container">
                        <img src="${post.url}" alt="${post.filename}">
                        <div class="like-button-wrapper">
                          <div class="like-button">
                            <input id="followed-heart-${post.id}" type="checkbox" ${post.is_liked_by_current_user ? 'checked' : ''} />
                            <label class="like" for="followed-heart-${post.id}">
                              <svg class="like-icon" fill-rule="nonzero" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                                <path d="m11.645 20.91-.007-.003-.022-.012a15.247 15.247 0 0 1-.383-.218 25.18 25.18 0 0 1-4.244-3.17C4.688 15.36 2.25 12.174 2.25 8.25 2.25 5.322 4.714 3 7.688 3A5.5 5.5 0 0 1 12 5.052 5.5 5.5 0 0 1 16.313 3c2.973 0 5.437 2.322 5.437 5.25 0 3.925-2.438 7.111-4.739 9.256a25.175 25.18 0 0 1-4.244 3.17 15.247 15.247 0 0 1-.383.219l-.022.012-.007.004-.003.001a.752.752 0 0 1-.704 0l-.003-.001Z"></path>
                              </svg>
                              <span class="like-text">Likes</span>
                            </label>
                            <span class="like-count one">${post.like_count}</span>
                            <span class="like-count two">${post.like_count}</span>
                          </div>
                        </div>
                      </div>
                      <div class="file-action-container">
                        <ul class="file-action-list">
                          <li class="file-action-item">
                            <button type="button" class="Btn download-image-btn" data-filename="${post.filename}">
                              <div class="sign">
                                <i class="fas fa-image logoIcon"></i>
                              </div>
                              <div class="text">Tải ảnh</div>
                            </button>
                          </li>
                         <li class="file-action-item">
                            <button type="button" class="Btn fb-share-btn" data-filename="${post.filename}" data-has-feedback="true">
                              <div class="sign">
                                <i class="fab fa-facebook logoIcon"></i>
                              </div>
                              <div class="text">Facebook</div>
                            </button>
                          </li>
                          <li class="file-action-item">
                            <button type="button" class="Btn file-copy-link-btn" data-url="${window.location.origin}/static/${post.filename}" data-has-feedback="true">
                              <div class="sign">
                                <i class="fas fa-link logoIcon"></i>
                              </div>
                              <div class="text">Copy Link</div>
                            </button>
                          </li>
                          ${post.tikz_code ? `
                          <li class="file-action-item">
                            <button type="button" class="Btn toggle-code-btn">
                              <div class="sign">
                                <i class="fas fa-code logoIcon"></i>
                              </div>
                              <div class="text">Xem Code</div>
                            </button>
                          </li>
                          ` : ''}
                        </ul>
                      </div>
                      
                      <!-- TikZ Code Section -->
                      ${post.tikz_code ? `
                      <div class="tikz-code-block" style="display:none; margin-top:10px;">
                        <div class="tikz-code-header">
                          <span>Code TikZ:</span>
                          <button class="copy-btn copy-tikz-btn">📋 Copy</button>
                        </div>
                        <div class="code-block">
                          <textarea class="tikz-cm" readonly>${post.tikz_code}</textarea>
                        </div>
                      </div>
                      ` : ''}
                    </div>
                `).join('');
                
                container.innerHTML = postsHTML;
                
                // Initialize like buttons for followed posts
                initializeFollowedPostLikeButtons();
            })
            .catch(error => {
                console.error('Error loading followed posts:', error);
                container.innerHTML = `
                    <div class="no-followed-posts">
                        <div class="no-followed-posts-icon">❌</div>
                        <h4>Lỗi tải dữ liệu</h4>
                        <p>Có lỗi xảy ra khi tải bài đăng. Vui lòng thử lại sau.</p>
                    </div>
                `;
            });
    }
    // Initialize like buttons for followed posts
    function initializeFollowedPostLikeButtons() {
        // Chỉ khởi tạo like buttons nếu đã đăng nhập
        if (!isLoggedIn) {
            return;
        }
        
        // Initialize like buttons
        document.querySelectorAll('input[id^="followed-heart-"]').forEach(function(checkbox) {
            checkbox.addEventListener('change', function() {
                const fileId = this.id.replace('followed-heart-', '');
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
                        
                        // // // console.log(`✅ Followed post ${data.message}: ${newCount} likes`);
                    } else {
                        // Revert UI if backend failed
                        this.checked = !isLiked;
                        // // // console.log(`❌ Followed post ${data.message}`);
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
    // Real-time synchronization for followed posts via polling
    function startFollowedPostsPolling() {
        // // // console.log('🔄 Starting followed posts polling...');
        const pollInterval = 15000; // 15 seconds
        
        // Clear any existing interval first
        if (followedPostsPollingInterval) {
            clearInterval(followedPostsPollingInterval);
        }
        
        followedPostsPollingInterval = setInterval(function() {
            // // // console.log('🔄 Polling followed posts...', new Date().toLocaleTimeString());
            const container = document.getElementById('followed-posts-container');
            if (!container) {
                // // // console.log('❌ Container not found, stopping polling');
                return;
            }
            
            // Kiểm tra flag toàn cục
            if (activeFeedbackCount > 0) {
                return;
            }
            
            // Fetch updated followed posts
            // // // console.log('🔄 Fetching /api/followed_posts...');
            fetch('/api/followed_posts')
                .then(response => {
                    // // // console.log('🔄 API response status:', response.status);
                    if (!response.ok) {
                        if (response.status === 401) {
                            // // // console.log('❌ User not logged in, stopping polling');
                            return null;
                        }
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(posts => {
                    if (!posts) return;
                    
                    // Check if there are new posts or updates
                    const hasNewPosts = posts.length !== currentPosts.length;
                    const hasUpdates = posts.some((post, index) => {
                        const currentPost = currentPosts[index];
                        return !currentPost || 
                               currentPost.like_count !== post.like_count ||
                               currentPost.is_liked_by_current_user !== post.is_liked_by_current_user;
                    });
                    
                    if (hasNewPosts || hasUpdates) {
                        // // // console.log('🔄 Followed posts updated, refreshing...');
                        loadFollowedPosts();
                    }
                })
                .catch(error => {
                    console.error('Followed posts polling error:', error);
                });
        }, pollInterval);
        
        // // // console.log('🔄 Started followed posts polling (15s interval)');
    }
    
    // Cleanup function for followed posts polling
    function stopFollowedPostsPolling() {
        if (followedPostsPollingInterval) {
            clearInterval(followedPostsPollingInterval);
            followedPostsPollingInterval = null;
            console.log('🔄 Followed posts polling stopped');
        }
    }
    
    // Cleanup function for like polling
    function stopLikePolling() {
        if (likePollingInterval) {
            clearInterval(likePollingInterval);
            likePollingInterval = null;
            console.log('🔄 Like polling stopped');
        }
    }
    
    // Master cleanup function for all polling
    function cleanupAllPolling() {
        stopFollowedPostsPolling();
        stopLikePolling();
        console.log('🔄 All polling cleanup completed');
    }
    
    // Expose cleanup function globally for manual cleanup if needed
    window.cleanupProfileFollowedPostsPolling = cleanupAllPolling;
    // Touch events for buttons (2-tap logic)
    function initializeTouchBtnEvents() {
        if (!document.documentElement.classList.contains('is-touch')) return;
        const originalHandlers = new Map();
        // Sử dụng event delegation thay vì gắn trực tiếp
        document.addEventListener('click', function(e) {
            // ==== Xử lý action-toggle-btn (nút ...) ====
            const actionToggleBtn = e.target.closest('.action-toggle-btn');
            if (actionToggleBtn) {
                const card = actionToggleBtn.closest('.file-card');
                if (card) {
                    // Đóng tất cả card khác
                    document.querySelectorAll('.file-card.active').forEach(other => {
                        if (other !== card) other.classList.remove('active');
                    });
                    // Toggle card hiện tại
                    card.classList.toggle('active');
                }
                return;
            }
            
            // ==== Xử lý các nút .Btn ====
            const btn = e.target.closest('.Btn');
            if (!btn) return;
            
            // Xử lý các nút .Btn trong card có class active
            if (btn.classList.contains('Btn')) {
                const card = btn.closest('.file-card');
                if (!card || !card.classList.contains('active')) return;
                // Lấy hoặc tạo tapCount
                if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
                
                const currentTapCount = parseInt(btn.dataset.tapCount);
                
                if (currentTapCount === 0) {
                    e.preventDefault();
                    e.stopPropagation();
                    e.stopImmediatePropagation();
                    // Reset các nút khác
                    card.querySelectorAll('.Btn').forEach(otherBtn => {
                        if (otherBtn !== btn) {
                            otherBtn.classList.remove('individual-active', 'ready-to-execute');
                            otherBtn.dataset.tapCount = '0';
                        }
                    });
                    btn.classList.add('individual-active', 'ready-to-execute');
                    btn.dataset.tapCount = '1';
                    // Auto reset sau 5s
                    setTimeout(() => {
                        if (btn.dataset.tapCount === '1') {
                            btn.classList.remove('individual-active', 'ready-to-execute');
                            btn.dataset.tapCount = '0';
                        }
                    }, 5000);
                    
                    return false;
                } 
                else if (currentTapCount === 1) {
                    // TAP 2: Execute action
                    
                    // Xử lý các nút dựa trên class names
                    // ✅ Xử lý cho nút "Facebook" (không có onclick)
                    if (btn.classList.contains('fb-share-btn') && btn.hasAttribute('data-filename')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        const filename = btn.getAttribute('data-filename');
                        const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                        copyToClipboardWithCustomFeedback(shareUrl, btn, 'Facebook', 'Đã copy!');
                        
                        // Giữ feedback hiển thị 2 giây trước khi reset
                        setTimeout(() => {
                            btn.dataset.tapCount = '0';
                            btn.classList.remove('individual-active', 'ready-to-execute');
                        }, 2000);
                        
                        return false;
                    }
                    // ✅ Xử lý cho nút "Copy Link" (không có onclick)
                    else if (btn.classList.contains('file-copy-link-btn') && btn.hasAttribute('data-url')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        const url = btn.getAttribute('data-url');
                        copyToClipboard(url, btn);
                        
                        // Giữ feedback hiển thị 2 giây trước khi reset
                        setTimeout(() => {
                            btn.dataset.tapCount = '0';
                            btn.classList.remove('individual-active', 'ready-to-execute');
                        }, 2000);
                        
                        return false;
                    }
                    // ✅ Thêm xử lý cho nút "Tải ảnh"
                    else if (btn.classList.contains('download-image-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        const filename = btn.getAttribute('data-filename');
                        if (filename) {
                            window.location.href = `/view_svg/${filename}`;
                        } else {
                            console.error('Không tìm thấy data-filename cho nút Tải ảnh');
                        }
                        // Reset trạng thái cho nút Tải ảnh ngay lập tức vì sẽ navigate
                        btn.dataset.tapCount = '0';
                        btn.classList.remove('individual-active', 'ready-to-execute');
                        
                        return false;
                    }
                    
                    // ✅ Thêm xử lý cho nút "Xem Code"
                    else if (btn.classList.contains('toggle-code-btn')) {
                        // Ngăn event delegation chạy
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        // Gọi function toggleTikzCode để hiển thị/ẩn code
                        toggleTikzCode(btn);
                        
                        // Giữ feedback hiển thị 1 giây trước khi reset
                        setTimeout(() => {
                            btn.dataset.tapCount = '0';
                            btn.classList.remove('individual-active', 'ready-to-execute');
                        }, 1000);
                        
                        return false;
                    }
                    
                    // ✅ Thêm xử lý cho nút "Copy TikZ Code"
                    else if (btn.classList.contains('copy-tikz-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        
                        // Gọi function copyTikzCode để copy code
                        copyTikzCode(btn);
                        
                        // Giữ feedback hiển thị 2 giây trước khi reset
                        setTimeout(() => {
                            btn.dataset.tapCount = '0';
                            btn.classList.remove('individual-active', 'ready-to-execute');
                        }, 2000);
                        
                        return false;
                    } 
                    else {
                        // Các nút khác: Giữ feedback hiển thị 1 giây
                        setTimeout(() => {
                            btn.dataset.tapCount = '0';
                            btn.classList.remove('individual-active', 'ready-to-execute');
                        }, 1000);
                    }
                    
                    return false;
                }
            }
        }, true); // Capture phase
    }
    // Function xử lý touch events đơn giản cho trường hợp chưa đăng nhập
    function initializeSimpleTouchEventsForNotLoggedIn() {
        if (!document.documentElement.classList.contains('is-touch')) return;
        if (isLoggedIn) return; // Chỉ xử lý cho trường hợp chưa đăng nhập
        // Logic 2-tap giống như đã đăng nhập
        document.addEventListener('click', function(e) {
            // ==== Xử lý action-toggle-btn (nút ...) cho trường hợp chưa đăng nhập ====
            const actionToggleBtn = e.target.closest('.action-toggle-btn');
            if (actionToggleBtn) {
                const card = actionToggleBtn.closest('.file-card');
                if (card) {
                    // Đóng tất cả card khác
                    document.querySelectorAll('.file-card.active').forEach(other => {
                        if (other !== card) other.classList.remove('active');
                    });
                    // Toggle card hiện tại
                    card.classList.toggle('active');
                }
                return;
            }
            
            // ==== Xử lý các nút .Btn ====
            const btn = e.target.closest('.Btn');
            if (!btn) return;
            
            const card = btn.closest('.file-card');
            if (!card) return;
            if (!card.classList.contains('active')) {
                // Mở menu trước, không thực thi lệnh ngay
                document.querySelectorAll('.file-card.active').forEach(other => {
                    if (other !== card) {
                        other.classList.remove('active');
                    }
                });
                card.classList.add('active');
                // Chỉ mở menu, chờ tap tiếp theo mới thực thi lệnh
                return;
            }
            
            // Chỉ xử lý cho trường hợp chưa đăng nhập
            if (isLoggedIn) return;
            
            // Lấy hoặc tạo tapCount
            if (!btn.dataset.tapCount) btn.dataset.tapCount = '0';
            const currentTapCount = parseInt(btn.dataset.tapCount);
            
            if (currentTapCount === 0) {
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                // Reset các nút khác
                card.querySelectorAll('.Btn').forEach(otherBtn => {
                    if (otherBtn !== btn) {
                        otherBtn.classList.remove('individual-active', 'ready-to-execute');
                        otherBtn.dataset.tapCount = '0';
                    }
                });
                btn.classList.add('individual-active', 'ready-to-execute');
                btn.dataset.tapCount = '1';
                // Auto reset sau 5s
                setTimeout(() => {
                    if (btn.dataset.tapCount === '1') {
                        btn.classList.remove('individual-active', 'ready-to-execute');
                        btn.dataset.tapCount = '0';
                    }
                }, 5000);
                
                return false;
            } 
            else if (currentTapCount === 1) {
                // TAP 2: Hiển thị modal đăng nhập
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                // Hiển thị modal đăng nhập
                const loginModal = document.getElementById('login-modal');
                if (loginModal) {
                    loginModal.style.display = 'flex';
                } else {
                    // Fallback: redirect to login
                    window.location.href = '/login/google';
                }
                // Giữ feedback hiển thị 1 giây trước khi reset
                setTimeout(() => {
                    btn.dataset.tapCount = '0';
                    btn.classList.remove('individual-active', 'ready-to-execute');
                }, 1000);
                
                return false;
            }
        }, true); // Capture phase
    }
    // Copy to clipboard functions
    function copyToClipboard(url, btn) {
        const card = btn.closest('.file-card');
        const actionContainer = card ? card.querySelector('.file-action-container') : null;
        
        // Kiểm tra xem có phải HTTPS hoặc localhost không
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        // Thử sử dụng navigator.clipboard trước (chỉ khi có quyền)
        if (navigator.clipboard && isSecureContext) {
            navigator.clipboard.writeText(url).then(function() {
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = 'Đã copy!';
                    activeFeedbackCount++; // Tăng counter
                    setTimeout(() => { 
                        textDiv.textContent = 'Copy Link'; 
                        activeFeedbackCount--; // Giảm counter
                    }, 3000);
                }
            }).catch(function(err) {
                console.error('❌ Clipboard API failed:', err);
                // // // console.log('🔄 Falling back to execCommand method');
                // Fallback to execCommand
                fallbackCopyToClipboard(url, btn);
            });
        } else {
            // Fallback cho các trình duyệt không hỗ trợ Clipboard API hoặc không có quyền
            // // // console.log('🔄 Using fallback copy method (no clipboard permission)');
            fallbackCopyToClipboard(url, btn);
        }
    }
    function fallbackCopyToClipboard(url, btn) {
        // // // console.log('🔄 Executing fallback copy method for URL:', url);
        
        const textArea = document.createElement('textarea');
        textArea.value = url;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        textArea.style.opacity = '0';
        document.body.appendChild(textArea);
        
        try {
            textArea.focus();
            textArea.select();
            // // // console.log('🔄 Text selected, attempting to copy...');
            
            const successful = document.execCommand('copy');
            // // // console.log('🔄 execCommand result:', successful);
            
            if (successful) {
                // // // console.log('✅ Fallback copy successful');
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = 'Đã copy!';
                    activeFeedbackCount++; // Tăng counter
                    setTimeout(() => { 
                        textDiv.textContent = 'Copy Link'; 
                        activeFeedbackCount--; // Giảm counter
                    }, 3000);
                }
            } else {
                console.error('❌ execCommand copy failed');
                // Thử hiển thị feedback ngay cả khi copy thất bại
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = 'Copy thất bại';
                    setTimeout(() => { 
                        textDiv.textContent = 'Copy Link'; 
                    }, 3000);
                }
                alert('Không thể copy link. Vui lòng copy thủ công: ' + url);
            }
        } catch (err) {
            console.error('❌ execCommand copy error:', err);
            // Thử hiển thị feedback ngay cả khi có lỗi
            const textDiv = btn.querySelector('.text');
            if (textDiv) {
                textDiv.textContent = 'Copy thất bại';
                setTimeout(() => { 
                    textDiv.textContent = 'Copy Link'; 
                }, 3000);
            }
            alert('Không thể copy link. Vui lòng copy thủ công: ' + url);
        } finally {
            // Luôn cleanup textarea
            if (document.body.contains(textArea)) {
                document.body.removeChild(textArea);
            }
        }
    }
    function copyToClipboardWithCustomFeedback(url, btn, originalText, feedbackText) {
        const card = btn.closest('.file-card');
        const actionContainer = card ? card.querySelector('.file-action-container') : null;
        
        // Kiểm tra xem có phải HTTPS hoặc localhost không
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        // Thử sử dụng navigator.clipboard trước (chỉ khi có quyền)
        if (navigator.clipboard && isSecureContext) {
            navigator.clipboard.writeText(url).then(function() {
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = feedbackText;
                    activeFeedbackCount++; // Tăng counter
                    
                    setTimeout(() => { 
                        textDiv.textContent = originalText; 
                        activeFeedbackCount--; // Giảm counter
                    }, 3000);
                }
            }).catch(function(err) {
                console.error('❌ Clipboard API failed (custom feedback):', err);
                // Fallback to execCommand
                fallbackCopyToClipboardWithCustomFeedback(url, btn, originalText, feedbackText);
            });
        } else {
            // Fallback cho các trình duyệt không hỗ trợ Clipboard API hoặc không có quyền
            // // console.log('🔄 Using fallback copy method with custom feedback (no clipboard permission)');
            fallbackCopyToClipboardWithCustomFeedback(url, btn, originalText, feedbackText);
        }
    }
    function fallbackCopyToClipboardWithCustomFeedback(url, btn, originalText, feedbackText) {
        const textArea = document.createElement('textarea');
        textArea.value = url;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            const successful = document.execCommand('copy');
            
            if (successful) {
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = feedbackText;
                    activeFeedbackCount++; // Tăng counter
                    
                    setTimeout(() => { 
                        textDiv.textContent = originalText; 
                        activeFeedbackCount--; // Giảm counter
                    }, 3000);
                }
            } else {
                console.error('❌ execCommand copy failed (custom feedback)');
                // Thử hiển thị feedback ngay cả khi copy thất bại
                const textDiv = btn.querySelector('.text');
                if (textDiv) {
                    textDiv.textContent = 'Copy thất bại';
                    setTimeout(() => { 
                        textDiv.textContent = originalText; 
                    }, 3000);
                }
                alert('Không thể copy link. Vui lòng copy thủ công: ' + url);
            }
        } catch (err) {
            console.error('❌ execCommand copy error (custom feedback):', err);
            // Thử hiển thị feedback ngay cả khi có lỗi
            const textDiv = btn.querySelector('.text');
            if (textDiv) {
                textDiv.textContent = 'Copy thất bại';
                setTimeout(() => { 
                    textDiv.textContent = originalText; 
                }, 3000);
            }
            alert('Không thể copy link. Vui lòng copy thủ công: ' + url);
        }
        
        document.body.removeChild(textArea);
    }
    // Toggle TikZ code function
    function toggleTikzCode(btn) {
        // // console.log('🔍 toggleTikzCode function called');
        // // console.log('🔍 btn:', btn);
        
        const card = btn.closest('.file-card');
        if (!card) {
            console.error('❌ Không tìm thấy card cho nút toggle code');
            return;
        }
        
        const codeBlock = card.querySelector('.tikz-code-block');
        if (!codeBlock) {
            console.error('❌ Không tìm thấy tikz-code-block trong card');
            return;
        }
        
        const textDiv = btn.querySelector('.text');
        if (!textDiv) {
            console.error('❌ Không tìm thấy text div trong button');
            return;
        }
        
        // // console.log('🔍 card:', card);
        // // console.log('🔍 codeBlock:', codeBlock);
        // // console.log('🔍 textDiv:', textDiv);
        
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
            // // console.log('Getting code from CodeMirror instance');
        } else {
            // // console.log('Getting code from original textarea');
        }
        
        // Kiểm tra xem có phải HTTPS hoặc localhost không
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
        
        if (navigator.clipboard && isSecureContext) {
            navigator.clipboard.writeText(code).then(function() {
                btn.textContent = 'Đã copy!';
                setTimeout(() => { 
                    btn.textContent = '📋 Copy'; 
                }, 2000);
            }).catch(function(err) {
                console.error('❌ Clipboard API failed:', err);
                fallbackCopyTikzCode(code, btn);
            });
        } else {
            // // console.log('🔄 Using fallback copy method for TikZ code (no clipboard permission)');
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
                btn.textContent = 'Đã copy!';
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
    // Initialize CodeMirror for TikZ code blocks
    function initializeCodeMirror() {
        document.querySelectorAll('.tikz-cm').forEach(function(textarea) {
            if (!textarea.CodeMirror) {
                const codeBlock = textarea.closest('.tikz-code-block');
                if (codeBlock) {
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
            } else {
                const cmInstance = textarea.CodeMirror;
                setTimeout(() => {
                    cmInstance.refresh();
                }, 100);
            }
        });
    }
    // Function to initialize Facebook share buttons
    function initializeFbShareButtons() {
        // Initialize Facebook share buttons for followed post cards
        const followedFbShareBtns = document.querySelectorAll('.followed-post-card .fb-share-btn');
        // // console.log('🔄 Initializing: Found', followedFbShareBtns.length, 'followed post fb-share-btn buttons');
        
        // Chỉ thêm event listener cho desktop khi chưa đăng nhập (mobile sẽ được xử lý bởi initializeTouchBtnEvents)
        if (!document.documentElement.classList.contains('is-touch') && !isLoggedIn) {
            followedFbShareBtns.forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const filename = btn.getAttribute('data-filename');
                    // // console.log('🔄 fb-share-btn clicked (desktop, not logged in), filename:', filename);
                    
                    if (!filename) {
                        console.error('❌ No filename found for fb-share-btn');
                        return;
                    }
                    
                    // Hiển thị modal đăng nhập
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) {
                        loginModal.style.display = 'flex';
                    } else {
                        // Fallback: redirect to login
                        window.location.href = '/login/google';
                    }
                });
            });
        } else {
            // // console.log('🔄 Skipping fb-share-btn initialization - mobile will be handled by initializeTouchBtnEvents, desktop logged in will be handled by Desktop logic');
        }
    }
    // Function to initialize copy link buttons
    function initializeCopyLinkButtons() {
        const followedCopyLinkBtns = document.querySelectorAll('.followed-post-card .file-copy-link-btn');
        // // console.log('🔄 Initializing: Found', followedCopyLinkBtns.length, 'followed post file-copy-link-btn buttons');
        
        // Chỉ thêm event listener cho desktop khi chưa đăng nhập (mobile sẽ được xử lý bởi initializeTouchBtnEvents)
        if (!document.documentElement.classList.contains('is-touch') && !isLoggedIn) {
            followedCopyLinkBtns.forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    const url = btn.getAttribute('data-url');
                    // // console.log('🔄 file-copy-link-btn clicked (desktop, not logged in), url:', url);
                    
                    if (!url) {
                        console.error('❌ No URL found for file-copy-link-btn');
                        return;
                    }
                    
                    // Hiển thị modal đăng nhập
                    const loginModal = document.getElementById('login-modal');
                    if (loginModal) {
                        loginModal.style.display = 'flex';
                    } else {
                        // Fallback: redirect to login
                        window.location.href = '/login/google';
                    }
                });
            });
        } else {
            // // console.log('🔄 Skipping copy link button initialization - mobile will be handled by initializeTouchBtnEvents, desktop logged in will be handled by Desktop logic');
        }
    }
    // Re-initialize buttons after a short delay to ensure DOM is ready
    setTimeout(function() {
        initializeFbShareButtons();
        initializeCopyLinkButtons();
        
        // ==== Thêm logic cho Desktop buttons (đã đăng nhập) ====
        if (!document.documentElement.classList.contains('is-touch') && isLoggedIn) {
            // // console.log('🖥️ Adding Desktop button logic (logged in)');
            
            // Thêm event listener cho Desktop buttons
            document.addEventListener('click', function(e) {
                const btn = e.target.closest('.followed-post-card .fb-share-btn, .followed-post-card .file-copy-link-btn');
                if (!btn) return;
                
                e.preventDefault();
                e.stopPropagation();
                
                if (btn.classList.contains('fb-share-btn')) {
                    const filename = btn.getAttribute('data-filename');
                    if (!filename) {
                        console.error('❌ No filename found for Desktop Facebook button');
                        return;
                    }
                    
                    const shareUrl = `${window.location.origin}/view_svg/${filename}`;
                    // // console.log('🖥️ Desktop Facebook Share URL:', shareUrl);
                    
                    // Sử dụng function copyToClipboard với custom feedback
                    copyToClipboardWithCustomFeedback(shareUrl, btn, 'Facebook', 'Đã copy!');
                    
                    // // console.log('✅ Desktop Facebook button: Link copied successfully');
                } else if (btn.classList.contains('file-copy-link-btn')) {
                    const url = btn.getAttribute('data-url');
                    if (!url) {
                        console.error('❌ No URL found for Desktop Copy Link button');
                        return;
                    }
                    
                    // // console.log('🖥️ Desktop Copy Link URL:', url);
                    
                    // Sử dụng function copyToClipboard
                    copyToClipboard(url, btn);
                    
                    // // console.log('✅ Desktop Copy Link button: Link copied successfully');
                }
            });
        }
    }, 100);
    // Real-time synchronization via polling for followed posts
    function startLikePolling() {
        const pollInterval = 10000; // 10 seconds
        let lastUpdateTime = Date.now();
        
        // // console.log('🔄 startLikePolling initialized with interval:', pollInterval, 'ms');
        
        // Clear any existing interval first
        if (likePollingInterval) {
            clearInterval(likePollingInterval);
        }
        
        likePollingInterval = setInterval(function() {
            // Get all file IDs on the page
            const fileCards = document.querySelectorAll('.followed-post-card');
            const fileIds = Array.from(fileCards).map(card => {
                return card.dataset.postId;
            }).filter(id => id); // Filter out undefined
            
            if (fileIds.length === 0) {
                // // console.log('🔄 No followed post cards found for polling');
                return;
            }
            
            // // console.log('🔄 Polling for', fileIds.length, 'followed posts:', fileIds);
            
            // Fetch updated like counts
            fetch('/api/like_counts', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    ids: fileIds
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data && typeof data === 'object') {
                    // Update UI for changed files
                    Object.keys(data).forEach(fileId => {
                        const fileData = data[fileId];
                        const fileCard = document.querySelector(`.followed-post-card[data-post-id="${fileId}"]`);
                        
                        if (fileCard && fileData) {
                            const likeButton = fileCard.querySelector('.like-button');
                            const likeCountSpan = fileCard.querySelector('.like-count.one');
                            const moveNumber = fileCard.querySelector('.like-count.two');
                            
                            // Cập nhật cho trường hợp đã đăng nhập (có like-button)
                            if (likeButton && likeCountSpan && moveNumber) {
                                const currentCount = parseInt(likeCountSpan.textContent) || 0;
                                const newLikeCount = fileData.like_count || 0;
                                
                                // Update like count if changed
                                if (currentCount !== newLikeCount) {
                                    likeCountSpan.textContent = newLikeCount;
                                    moveNumber.textContent = newLikeCount;
                                    // // console.log(`🔄 Real-time update: Followed post ${fileId} now has ${newLikeCount} likes (logged in)`);
                                    
                                    // Add visual feedback
                                    likeButton.style.animation = 'pulse 0.5s ease-in-out';
                                    setTimeout(() => {
                                        likeButton.style.animation = '';
                                    }, 500);
                                }
                                
                                // Update checkbox state if changed
                                const checkbox = likeButton.querySelector('input[type="checkbox"]');
                                if (checkbox && fileData.is_liked_by_current_user !== undefined) {
                                    const currentChecked = checkbox.checked;
                                    const newChecked = fileData.is_liked_by_current_user;
                                    
                                    if (currentChecked !== newChecked) {
                                        checkbox.checked = newChecked;
                                        // // console.log(`🔄 Real-time update: Followed post ${fileId} like status changed to ${newChecked}`);
                                        
                                        // Trigger change event to update UI styling
                                        const event = new Event('change', { bubbles: true });
                                        checkbox.dispatchEvent(event);
                                    }
                                }
                            }
                        }
                    });
                    
                    lastUpdateTime = Date.now();
                }
            })
            .catch(error => {
                console.error('Followed posts polling error:', error);
            });
        }, pollInterval);
    }
    // Modern event handling to avoid deprecated warnings
    if (typeof window !== 'undefined') {
        // Use modern APIs instead of deprecated ones
        window.addEventListener('load', function() {
            // // console.log('✅ Page loaded successfully');
        });
        
        // Cleanup polling when user navigates away from page
        window.addEventListener('pagehide', cleanupAllPolling);
        window.addEventListener('beforeunload', cleanupAllPolling);
        
        // Cleanup polling when page becomes hidden (mobile browsers)
        document.addEventListener('visibilitychange', function() {
            if (document.hidden) {
                cleanupAllPolling();
            } else {
                // Restart polling when page becomes visible again
                if (isLoggedIn) {
                    // Only restart followed posts polling if user is owner
                    if (isOwner) {
                        startFollowedPostsPolling();
                    }
                    // Always restart like polling for logged in users
                    startLikePolling();
                }
            }
        });
        
        // Modern DOM observation using MutationObserver
        if (typeof MutationObserver !== 'undefined') {
            const observer = new MutationObserver(function(mutations) {
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        // Handle DOM changes here if needed
                        // This replaces the deprecated DOMNodeInserted event
                        // Currently no specific handling needed for this page
                    }
                });
            });
            
            // Start observing when DOM is ready
            if (document.body) {
                observer.observe(document.body, {
                    childList: true,
                    subtree: true
                });
            } else {
                // Wait for DOM to be ready
                document.addEventListener('DOMContentLoaded', function() {
                    observer.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                });
            }
            
            // // console.log('✅ Modern MutationObserver initialized');
        }
    }
})();
