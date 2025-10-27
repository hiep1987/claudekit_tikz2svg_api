/**
 * COMMENTS SYSTEM - JAVASCRIPT
 * Version: 1.2.1 Final
 * Date: 2025-10-22
 * 
 * Production-ready JavaScript for Comments feature with:
 * - State management
 * - API integration (AJAX)
 * - Optimistic UI updates
 * - MathJax rendering
 * - Nested replies support
 * - Like/Unlike functionality
 * - Edit/Delete comments
 * - Pagination
 * - Error handling
 * - Debouncing
 * - Loading skeletons
 */

(function() {
    'use strict';
    
    // =====================================================
    // STATE MANAGEMENT
    // =====================================================
    
    const CommentsState = {
        filename: null,
        isLoggedIn: false,
        currentUserId: null,
        currentUserAvatar: null,
        currentUserAvatarFallback: null,
        currentUserName: null,
        currentUserVerified: false,
        verifiedIconUrl: '/static/identity-verification-icon.svg',
        apiBasePath: '/api/comments',
        comments: [],
        userLikes: [],
        pagination: {
            currentPage: 1,
            perPage: 20,
            totalPages: 1,
            totalComments: 0
        },
        loading: false,
        error: null
    };
    
    // =====================================================
    // DOM ELEMENTS
    // ===================================================== 

    const elements = {};
    
    function initElements() {
        // Data
        const commentsData = document.getElementById('comments-data-json');
        if (commentsData) {
            const data = JSON.parse(commentsData.textContent);
            Object.assign(CommentsState, data);
        }
        
        // Containers
        elements.commentsSection = document.getElementById('comments-section');
        elements.commentsCountBadge = document.getElementById('comments-count-badge');
        elements.commentsLoading = document.getElementById('comments-loading');
        elements.commentsEmpty = document.getElementById('comments-empty');
        elements.commentsContainer = document.getElementById('comments-container');
        
        // Form elements
        elements.newCommentInput = document.getElementById('new-comment-input');
        elements.commentCharCurrent = document.getElementById('comment-char-current');
        elements.submitCommentBtn = document.getElementById('submit-comment-btn');
        elements.commentFormMessage = document.getElementById('comment-form-message');
        
        // Login links
        elements.loginToCommentLink = document.getElementById('login-to-comment-link');
        elements.loginToCommentEmpty = document.getElementById('login-to-comment-empty');
        
        // Pagination
        elements.commentsPagination = document.getElementById('comments-pagination');
        elements.currentPageEl = document.getElementById('current-page');
        elements.totalPagesEl = document.getElementById('total-pages');
        elements.prevBtn = document.getElementById('comments-prev-btn');
        elements.nextBtn = document.getElementById('comments-next-btn');
        
        // Template
        elements.commentTemplate = document.getElementById('comment-template');
    }
    
    // =====================================================
    // UTILITY FUNCTIONS
    // =====================================================
    
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    /**
     * Render comment text with TikZ code block support
     * Syntax: \code{...TikZ code...}
     * Also supports MathJax: $inline$ and $$display$$
     * Handles nested braces correctly by counting { and }
     */
    function renderCommentText(text) {
        if (!text) return '';
        
        // First, escape HTML to prevent XSS
        let escaped = escapeHtml(text);
        
        // Process TikZ code blocks: \code{...}
        // Use custom parser to handle nested braces
        let result = '';
        let i = 0;
        
        while (i < escaped.length) {
            // Look for \code{
            const codeStart = escaped.indexOf('\\code{', i);
            
            if (codeStart === -1) {
                // No more code blocks, append rest and convert line breaks
                const remaining = escaped.substring(i);
                result += remaining.replace(/\n/g, '<br>');
                break;
            }
            
            // Append text before \code{ and convert line breaks
            const textBefore = escaped.substring(i, codeStart);
            result += textBefore.replace(/\n/g, '<br>');
            
            // Find matching closing brace by counting
            let braceCount = 1;
            let codeEnd = codeStart + 6; // Start after \code{
            
            while (codeEnd < escaped.length && braceCount > 0) {
                if (escaped[codeEnd] === '{' && escaped[codeEnd - 1] !== '\\') {
                    braceCount++;
                } else if (escaped[codeEnd] === '}' && escaped[codeEnd - 1] !== '\\') {
                    braceCount--;
                }
                codeEnd++;
            }
            
            if (braceCount === 0) {
                // Found matching brace
                const code = escaped.substring(codeStart + 6, codeEnd - 1);
                
                // Unescape the code content for proper display
                const unescapedCode = code
                    .replace(/&lt;/g, '<')
                    .replace(/&gt;/g, '>')
                    .replace(/&quot;/g, '"')
                    .replace(/&#039;/g, "'")
                    .replace(/&amp;/g, '&');
                
                // Trim leading/trailing whitespace to prevent gap at top/bottom
                const trimmedCode = unescapedCode.trim();
                
                // Re-escape for safe HTML display (preserve \n for <pre>)
                const safeCode = trimmedCode
                    .replace(/&/g, '&amp;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
                
                // Append code block (DON'T convert \n to <br> inside code!)
                result += `<div class="tikz-code-block"><div class="code-header"><span class="code-label">TikZ Code</span><button class="code-copy-btn" onclick="copyTikzCode(this)" title="Copy code"><span class="copy-icon">📋</span></button></div><pre class="tikz-code"><code>${safeCode}</code></pre></div>`;
                
                i = codeEnd;
            } else {
                // Unmatched braces, treat as plain text
                result += '\\code{';
                i = codeStart + 6;
            }
        }
        
        return result;
    }
    
    /**
     * Copy TikZ code to clipboard
     */
    window.copyTikzCode = function(button) {
        const codeBlock = button.closest('.tikz-code-block');
        const codeElement = codeBlock.querySelector('code');
        const code = codeElement.textContent;
        
        navigator.clipboard.writeText(code).then(() => {
            const icon = button.querySelector('.copy-icon');
            const originalText = icon.textContent;
            icon.textContent = '✅';
            
            setTimeout(() => {
                icon.textContent = originalText;
            }, 2000);
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Không thể copy code');
        });
    };
    
    function formatTimeAgo(isoString) {
        if (!isoString) return '';
        
        try {
            // Parse the timestamp (assume it's in Vietnam timezone from server)
            const serverTime = new Date(isoString);
            
            // Get current time in Vietnam timezone
            const now = new Date();
            const vnNow = new Date(now.toLocaleString("en-US", {timeZone: "Asia/Ho_Chi_Minh"}));
            
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
            if (diffDay < 7) return `${diffDay} ngày trước`;
            
            // For older dates, show actual date in Vietnam timezone
            return serverTime.toLocaleDateString('vi-VN', {
                timeZone: 'Asia/Ho_Chi_Minh'
            });
            
        } catch (error) {
            console.error('Error formatting comment time:', error);
            return isoString; // Fallback to original timestamp
        }
    }
    
    function showMessage(element, message, type = 'success') {
        if (!element) return;
        
        element.textContent = message;
        element.className = `comment-message ${type}`;
        element.style.display = 'block';
        
        setTimeout(() => {
            element.style.display = 'none';
        }, 5000);
    }
    
    function showLoadingSkeleton() {
        if (elements.commentsLoading) {
            elements.commentsLoading.style.display = 'block';
        }
        if (elements.commentsEmpty) {
            elements.commentsEmpty.style.display = 'none';
        }
        if (elements.commentsContainer) {
            elements.commentsContainer.innerHTML = '';
        }
    }
    
    function hideLoadingSkeleton() {
        if (elements.commentsLoading) {
            elements.commentsLoading.style.display = 'none';
        }
    }
    
    function triggerMathJax(element) {
        if (window.MathJax && window.MathJax.typesetPromise) {
            window.MathJax.typesetPromise([element]).catch(err => {
                console.error('MathJax rendering error:', err);
            });
        }
    }
    
    // =====================================================
    // API CALLS
    // =====================================================
    
    async function fetchComments(page = 1) {
        CommentsState.loading = true;
        showLoadingSkeleton();
        
        try {
            const url = `${CommentsState.apiBasePath}/${CommentsState.filename}?page=${page}&per_page=${CommentsState.pagination.perPage}&sort=newest`;
            const response = await fetch(url);
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const result = await response.json();
            
            if (result.success && result.data) {
                CommentsState.comments = result.data.comments || [];
                CommentsState.userLikes = result.data.user_likes || [];
                
                // Normalize pagination (handle both snake_case and camelCase)
                const paginationData = result.data.pagination || {};
                CommentsState.pagination = {
                    ...CommentsState.pagination,
                    currentPage: paginationData.current_page || paginationData.currentPage || 1,
                    perPage: paginationData.per_page || paginationData.perPage || 20,
                    totalPages: paginationData.total_pages || paginationData.totalPages || 1,
                    totalComments: paginationData.total_comments || paginationData.totalComments || 0
                };
                
                
                renderComments();
                updatePagination();
            } else {
                throw new Error(result.message || 'Không thể tải bình luận');
            }
        } catch (error) {
            console.error('Fetch comments error:', error);
            CommentsState.error = error.message;
            showEmptyState();
        } finally {
            CommentsState.loading = false;
            hideLoadingSkeleton();
        }
    }
    
    async function createComment(commentText, parentCommentId = null) {
        try {
            const url = `${CommentsState.apiBasePath}/${CommentsState.filename}`;
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    comment_text: commentText,
                    parent_comment_id: parentCommentId
                })
            });
            
            const result = await response.json();
            
            if (result.success && result.data && result.data.comment) {
                return { success: true, comment: result.data.comment };
            } else {
                return { success: false, message: result.message || 'Không thể gửi bình luận' };
            }
        } catch (error) {
            console.error('Create comment error:', error);
            return { success: false, message: 'Lỗi kết nối. Vui lòng thử lại.' };
        }
    }
    
    async function updateComment(commentId, newText) {
        try {
            const url = `${CommentsState.apiBasePath}/${commentId}`;
            const response = await fetch(url, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    comment_text: newText
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                return { success: true, commentText: result.data.comment_text };
            } else {
                return { success: false, message: result.message || 'Không thể cập nhật bình luận' };
            }
        } catch (error) {
            console.error('Update comment error:', error);
            return { success: false, message: 'Lỗi kết nối. Vui lòng thử lại.' };
        }
    }
    
    async function deleteComment(commentId) {
        try {
            const url = `${CommentsState.apiBasePath}/${commentId}`;
            const response = await fetch(url, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (result.success) {
                return { success: true };
            } else {
                return { success: false, message: result.message || 'Không thể xóa bình luận' };
            }
        } catch (error) {
            console.error('Delete comment error:', error);
            return { success: false, message: 'Lỗi kết nối. Vui lòng thử lại.' };
        }
    }
    
    async function toggleLike(commentId) {
        try {
            const url = `${CommentsState.apiBasePath}/${commentId}/like`;
            const response = await fetch(url, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success && result.data) {
                return { 
                    success: true, 
                    liked: result.data.liked,
                    likesCount: result.data.likes_count
                };
            } else {
                return { success: false, message: result.message || 'Không thể thích bình luận' };
            }
        } catch (error) {
            console.error('Toggle like error:', error);
            return { success: false, message: 'Lỗi kết nối. Vui lòng thử lại.' };
        }
    }
    
    // =====================================================
    // RENDER FUNCTIONS
    // =====================================================
    
    function renderComments() {
        if (!elements.commentsContainer) return;
        
        elements.commentsContainer.innerHTML = '';
        
        if (CommentsState.comments.length === 0) {
            showEmptyState();
            return;
        }
        
        if (elements.commentsEmpty) {
            elements.commentsEmpty.style.display = 'none';
        }
        
        
        CommentsState.comments.forEach(comment => {
            const commentEl = createCommentElement(comment);
            elements.commentsContainer.appendChild(commentEl);
        });
        
        // Trigger MathJax rendering
        triggerMathJax(elements.commentsContainer);
        
        // Update count badge
        updateCommentsCount();
    }
    
    function createCommentElement(comment, isReply = false) {
        if (!elements.commentTemplate) return null;
        
        const template = elements.commentTemplate.content.cloneNode(true);
        const commentDiv = template.querySelector('.comment');
        
        // Set data attribute
        commentDiv.dataset.commentId = comment.id;
        
        // Avatar
        const avatarImg = commentDiv.querySelector('.comment-avatar');
        const avatarFallback = commentDiv.querySelector('.comment-user-avatar-fallback');
        
        // Check if avatar exists and is not empty
        const hasValidAvatar = comment.avatar && comment.avatar.trim() !== '' && comment.avatar !== 'None';
        
        if (hasValidAvatar) {
            // Use avatar image
            const avatarPath = comment.avatar.startsWith('/static/') ? comment.avatar : `/static/avatars/${comment.avatar}`;
            avatarImg.src = avatarPath;
            avatarImg.alt = comment.username || 'User';
            avatarImg.style.display = 'block';
            avatarFallback.style.display = 'none';
        } else {
            // Use fallback with first letter
            avatarImg.style.display = 'none';
            avatarFallback.textContent = (comment.username || comment.email || 'U')[0].toUpperCase();
            avatarFallback.style.display = 'flex';
        }
        
        // Author
        const author = commentDiv.querySelector('.comment-author');
        author.textContent = comment.username || 'Anonymous';
        
        // Verified icon
        if (comment.identity_verified) {
            const verifiedIcon = commentDiv.querySelector('.verified-icon');
            if (verifiedIcon) {
                verifiedIcon.src = CommentsState.verifiedIconUrl || '/static/identity-verification-icon.svg';
                verifiedIcon.style.display = 'inline-block';
            }
        }
        
        // Timestamp
        const timestamp = commentDiv.querySelector('.comment-timestamp');
        timestamp.textContent = formatTimeAgo(comment.created_at);
        
        // Comment text with TikZ code block support
        const commentText = commentDiv.querySelector('.comment-text');
        commentText.innerHTML = renderCommentText(comment.comment_text);
        
        // Edited label
        if (comment.updated_at && comment.updated_at !== comment.created_at) {
            const editedLabel = commentDiv.querySelector('.comment-edited-label');
            editedLabel.style.display = 'inline';
        }
        
        // Like button
        const likeBtn = commentDiv.querySelector('.comment-like-btn');
        const likeCount = commentDiv.querySelector('.like-count');
        likeCount.textContent = comment.likes_count || 0;
        
        if (CommentsState.userLikes.includes(comment.id)) {
            likeBtn.classList.add('liked');
        }
        
        // Actions menu (only for owner)
        const actionsMenu = commentDiv.querySelector('.comment-actions-menu');
        if (CommentsState.currentUserId === comment.user_id) {
            actionsMenu.style.display = 'block';
        } else {
            actionsMenu.style.display = 'none';
        }
        
        // Reply button (allow unlimited nested replies)
        const replyBtn = commentDiv.querySelector('.comment-reply-btn');
        // Removed restriction - now allows infinite nesting levels
        
        // Render nested replies
        if (comment.replies && comment.replies.length > 0) {
            const repliesContainer = commentDiv.querySelector('.comment-replies');
            
            if (!repliesContainer) {
                console.error(`❌ No .comment-replies container found for comment ${comment.id}`);
                return commentDiv;
            }
            
            comment.replies.forEach((reply) => {
                const replyEl = createCommentElement(reply, true);
                repliesContainer.appendChild(replyEl);
            });
        }
        
        // Attach event listeners
        attachCommentEventListeners(commentDiv, comment);
        
        return commentDiv;
    }
    
    function showEmptyState() {
        if (elements.commentsEmpty) {
            elements.commentsEmpty.style.display = 'block';
        }
        if (elements.commentsContainer) {
            elements.commentsContainer.innerHTML = '';
        }
        updateCommentsCount();
    }
    
    function updateCommentsCount() {
        if (elements.commentsCountBadge) {
            elements.commentsCountBadge.textContent = CommentsState.pagination.totalComments || 0;
        }
    }
    
    function updatePagination() {
        if (!elements.commentsPagination) return;
        
        const { currentPage, totalPages } = CommentsState.pagination;
        
        if (totalPages <= 1) {
            elements.commentsPagination.style.display = 'none';
            return;
        }
        
        elements.commentsPagination.style.display = 'flex';
        
        if (elements.currentPageEl) {
            elements.currentPageEl.textContent = currentPage;
        }
        if (elements.totalPagesEl) {
            elements.totalPagesEl.textContent = totalPages;
        }
        
        if (elements.prevBtn) {
            elements.prevBtn.disabled = currentPage <= 1;
        }
        if (elements.nextBtn) {
            elements.nextBtn.disabled = currentPage >= totalPages;
        }
    }
    
    // =====================================================
    // EVENT HANDLERS
    // =====================================================
    
    function attachCommentEventListeners(commentDiv, comment) {
        // Menu toggle
        const menuBtn = commentDiv.querySelector('.comment-menu-btn');
        const dropdown = commentDiv.querySelector('.comment-dropdown');
        
        if (menuBtn && dropdown) {
            menuBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
            });
            
            // Close dropdown when clicking outside
            document.addEventListener('click', () => {
                dropdown.style.display = 'none';
            });
        }
        
        // Edit button
        const editBtn = commentDiv.querySelector('.edit-comment-btn');
        if (editBtn) {
            editBtn.addEventListener('click', () => {
                handleEditComment(commentDiv, comment);
            });
        }
        
        // Delete button
        const deleteBtn = commentDiv.querySelector('.delete-comment-btn');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', () => {
                handleDeleteComment(comment.id);
            });
        }
        
        // Like button
        const likeBtn = commentDiv.querySelector('.comment-like-btn');
        if (likeBtn) {
            likeBtn.addEventListener('click', () => {
                handleLikeComment(commentDiv, comment.id);
            });
        }
        
        // Reply button
        const replyBtn = commentDiv.querySelector('.comment-reply-btn');
        if (replyBtn) {
            replyBtn.addEventListener('click', () => {
                handleReplyComment(commentDiv, comment);
            });
        }
    }
    
    async function handleSubmitComment() {
        if (!CommentsState.isLoggedIn) {
            showMessage(elements.commentFormMessage, 'Vui lòng đăng nhập để bình luận', 'error');
            return;
        }
        
        const commentText = elements.newCommentInput.value.trim();
        
        if (!commentText) {
            showMessage(elements.commentFormMessage, 'Nội dung bình luận không được để trống', 'error');
            return;
        }
        
        if (commentText.length > 5000) {
            showMessage(elements.commentFormMessage, 'Bình luận không được dài quá 5000 ký tự', 'error');
            return;
        }
        
        // Disable button
        elements.submitCommentBtn.disabled = true;
        elements.submitCommentBtn.textContent = '⏳ Đang gửi...';
        
        const result = await createComment(commentText);
        
        if (result.success) {
            // Clear input
            elements.newCommentInput.value = '';
            elements.commentCharCurrent.textContent = '0';
            
            // Clear preview
            const previewContent = document.getElementById('comment-preview-content');
            if (previewContent) {
                previewContent.textContent = 'Nhập bình luận để xem preview...';
                previewContent.style.color = '#a0aec0';
            }
            
            // Show success message
            showMessage(elements.commentFormMessage, '✅ Đã gửi bình luận thành công!', 'success');
            
            // Reload comments
            await fetchComments(CommentsState.pagination.currentPage);
        } else {
            showMessage(elements.commentFormMessage, result.message, 'error');
        }
        
        // Re-enable button
        elements.submitCommentBtn.disabled = false;
        elements.submitCommentBtn.innerHTML = '<span class="btn-icon">📨</span> Gửi bình luận';
    }
    
    function handleEditComment(commentDiv, comment) {
        const commentBody = commentDiv.querySelector('.comment-body');
        const commentTextEl = commentBody.querySelector('.comment-text');
        const editForm = commentBody.querySelector('.comment-edit-form');
        const editTextarea = editForm.querySelector('.comment-edit-textarea');
        const cancelBtn = editForm.querySelector('.comment-btn-cancel');
        const saveBtn = editForm.querySelector('.comment-btn-save');
        
        // Hide text, show form
        commentTextEl.style.display = 'none';
        editForm.style.display = 'block';
        editTextarea.value = comment.comment_text;
        editTextarea.focus();
        
        // Cancel handler
        cancelBtn.onclick = () => {
            commentTextEl.style.display = 'block';
            editForm.style.display = 'none';
        };
        
        // Save handler
        saveBtn.onclick = async () => {
            const newText = editTextarea.value.trim();
            
            if (!newText) {
                alert('Nội dung bình luận không được để trống');
                return;
            }
            
            if (newText.length > 5000) {
                alert('Bình luận không được dài quá 5000 ký tự');
                return;
            }
            
            saveBtn.disabled = true;
            saveBtn.textContent = 'Đang lưu...';
            
            const result = await updateComment(comment.id, newText);
            
            if (result.success) {
                // Update comment text with TikZ code block support
                commentTextEl.innerHTML = renderCommentText(newText);
                
                // Update state
                comment.comment_text = newText;
                
                // Show edited label
                const editedLabel = commentDiv.querySelector('.comment-edited-label');
                editedLabel.style.display = 'inline';
                
                // Hide form, show text
                commentTextEl.style.display = 'block';
                editForm.style.display = 'none';
                
                // Trigger MathJax
                triggerMathJax(commentTextEl);
            } else {
                alert(result.message);
            }
            
            saveBtn.disabled = false;
            saveBtn.textContent = 'Lưu';
        };
    }
    
    async function handleDeleteComment(commentId) {
        if (!confirm('Bạn có chắc chắn muốn xóa bình luận này?')) {
            return;
        }
        
        const result = await deleteComment(commentId);
        
        if (result.success) {
            // Reload comments
            await fetchComments(CommentsState.pagination.currentPage);
        } else {
            alert(result.message);
        }
    }
    
    async function handleLikeComment(commentDiv, commentId) {
        if (!CommentsState.isLoggedIn) {
            alert('Vui lòng đăng nhập để thích bình luận');
            return;
        }
        
        const likeBtn = commentDiv.querySelector('.comment-like-btn');
        const likeCount = commentDiv.querySelector('.like-count');
        
        // Optimistic UI update
        const wasLiked = likeBtn.classList.contains('liked');
        const currentCount = parseInt(likeCount.textContent) || 0;
        
        if (wasLiked) {
            likeBtn.classList.remove('liked');
            likeCount.textContent = Math.max(0, currentCount - 1);
        } else {
            likeBtn.classList.add('liked');
            likeCount.textContent = currentCount + 1;
        }
        
        // API call
        const result = await toggleLike(commentId);
        
        if (result.success) {
            // Update state
            if (result.liked) {
                if (!CommentsState.userLikes.includes(commentId)) {
                    CommentsState.userLikes.push(commentId);
                }
            } else {
                CommentsState.userLikes = CommentsState.userLikes.filter(id => id !== commentId);
            }
            
            // Update UI with actual data
            likeCount.textContent = result.likesCount;
            if (result.liked) {
                likeBtn.classList.add('liked');
            } else {
                likeBtn.classList.remove('liked');
            }
        } else {
            // Revert optimistic update on failure
            if (wasLiked) {
                likeBtn.classList.add('liked');
                likeCount.textContent = currentCount;
            } else {
                likeBtn.classList.remove('liked');
                likeCount.textContent = currentCount;
            }
            alert(result.message);
        }
    }
    
    function handleReplyComment(commentDiv, parentComment) {
        if (!CommentsState.isLoggedIn) {
            alert('Vui lòng đăng nhập để trả lời');
            return;
        }
        
        const replyForm = commentDiv.querySelector('.comment-reply-form');
        const replyTextarea = replyForm.querySelector('.reply-textarea');
        const replyPreview = replyForm.querySelector('.reply-preview-content');
        const cancelBtn = replyForm.querySelector('.comment-btn-cancel');
        const submitBtn = replyForm.querySelector('.comment-btn-submit');
        
        // Update reply preview function
        const updateReplyPreview = debounce(() => {
            if (!replyPreview) return;
            
            const text = replyTextarea.value.trim();
            
            if (!text) {
                replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
                replyPreview.style.color = '#a0aec0';
                return;
            }
            
            // Render with TikZ code block support
            replyPreview.innerHTML = renderCommentText(text);
            replyPreview.style.color = '#1a202c';
            
            // Render MathJax if available
            if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
                MathJax.typesetPromise([replyPreview]).catch((err) => {
                    console.warn('MathJax rendering error:', err);
                });
            }
        }, 300);
        
        // Show form
        replyForm.style.display = 'block';
        replyTextarea.focus();
        
        // Add preview listener
        replyTextarea.addEventListener('input', updateReplyPreview);
        
        // Cancel handler
        cancelBtn.onclick = () => {
            replyForm.style.display = 'none';
            replyTextarea.value = '';
            if (replyPreview) {
                replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
                replyPreview.style.color = '#a0aec0';
            }
            replyTextarea.removeEventListener('input', updateReplyPreview);
        };
        
        // Submit handler
        submitBtn.onclick = async () => {
            const replyText = replyTextarea.value.trim();
            
            if (!replyText) {
                alert('Nội dung trả lời không được để trống');
                return;
            }
            
            if (replyText.length > 5000) {
                alert('Trả lời không được dài quá 5000 ký tự');
                return;
            }
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Đang gửi...';
            
            const result = await createComment(replyText, parentComment.id);
            
            if (result.success) {
                // Reload comments
                await fetchComments(CommentsState.pagination.currentPage);
                
                // Hide form and clear preview
                replyForm.style.display = 'none';
                replyTextarea.value = '';
                if (replyPreview) {
                    replyPreview.textContent = 'Nhập câu trả lời để xem preview...';
                    replyPreview.style.color = '#a0aec0';
                }
                replyTextarea.removeEventListener('input', updateReplyPreview);
            } else {
                alert(result.message);
            }
            
            submitBtn.disabled = false;
            submitBtn.textContent = 'Gửi';
        };
    }
    
    // =====================================================
    // CHARACTER COUNTER
    // =====================================================
    
    function updateCharCounter() {
        if (!elements.newCommentInput || !elements.commentCharCurrent) return;
        
        const length = elements.newCommentInput.value.length;
        elements.commentCharCurrent.textContent = length;
        
        // Warning color if near limit
        if (length > 4500) {
            elements.commentCharCurrent.style.color = 'var(--error-text)';
        } else {
            elements.commentCharCurrent.style.color = 'var(--text-primary)';
        }
        
        // Update preview
        updateCommentPreview();
    }
    
    function updateCommentPreview() {
        const previewContent = document.getElementById('comment-preview-content');
        if (!previewContent || !elements.newCommentInput) return;
        
        const text = elements.newCommentInput.value.trim();
        
        if (!text) {
            previewContent.textContent = 'Nhập bình luận để xem preview...';
            previewContent.style.color = '#a0aec0';
            return;
        }
        
        // Render with TikZ code block support
        previewContent.innerHTML = renderCommentText(text);
        previewContent.style.color = '#1a202c';
        
        // Render MathJax if available
        if (typeof MathJax !== 'undefined' && MathJax.typesetPromise) {
            MathJax.typesetPromise([previewContent]).catch((err) => {
                console.warn('MathJax rendering error:', err);
            });
        }
    }
    
    // =====================================================
    // PAGINATION HANDLERS
    // =====================================================
    
    function handlePrevPage() {
        if (CommentsState.pagination.currentPage > 1) {
            fetchComments(CommentsState.pagination.currentPage - 1);
        }
    }
    
    function handleNextPage() {
        if (CommentsState.pagination.currentPage < CommentsState.pagination.totalPages) {
            fetchComments(CommentsState.pagination.currentPage + 1);
        }
    }
    
    // =====================================================
    // LOGIN HANDLERS
    // =====================================================
    
    function handleLoginClick(e) {
        e.preventDefault();
        
        // Trigger login modal (if exists)
        const loginModal = document.getElementById('login-modal');
        if (loginModal) {
            loginModal.style.display = 'flex';
        } else {
            // Fallback: redirect to Google OAuth
            window.location.href = '/login/google';
        }
    }
    
    // =====================================================
    // INITIALIZATION
    // =====================================================
    
    function init() {
        console.log('🚀 Comments System initializing...');
        
        initElements();
        
        if (!CommentsState.filename) {
            console.error('❌ No filename found');
            return;
        }
        
        // Attach event listeners
        if (elements.newCommentInput) {
            elements.newCommentInput.addEventListener('input', debounce(updateCharCounter, 100));
        }
        
        if (elements.submitCommentBtn) {
            elements.submitCommentBtn.addEventListener('click', handleSubmitComment);
        }
        
        if (elements.loginToCommentLink) {
            elements.loginToCommentLink.addEventListener('click', handleLoginClick);
        }
        
        if (elements.loginToCommentEmpty) {
            elements.loginToCommentEmpty.addEventListener('click', handleLoginClick);
        }
        
        if (elements.prevBtn) {
            elements.prevBtn.addEventListener('click', handlePrevPage);
        }
        
        if (elements.nextBtn) {
            elements.nextBtn.addEventListener('click', handleNextPage);
        }
        
        // Load comments
        fetchComments(1);
        
        
        console.log('✅ Comments System initialized');
    }
    
    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();

