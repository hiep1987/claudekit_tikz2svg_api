// View SVG Page JavaScript (modular, no globals)
(function() {
  'use strict';

  function showLoginModal() {
    const modal = document.getElementById('login-modal');
    if (modal) modal.style.display = 'flex';
  }

  function requireLogin(callback) {
    const isLoggedIn = document.body.getAttribute('data-is-logged-in') === 'true';
    if (isLoggedIn) {
      callback();
    } else {
      showLoginModal();
    }
  }

  function copyToClipboard(text, button, originalText) {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(text).then(() => {
        // Track copy action
        if (window.analytics) {
          window.analytics.trackFileCopy('link', 'clipboard');
        }
        
        button.textContent = '✅ Đã copy!';
        setTimeout(() => { button.textContent = originalText; }, 2000);
      });
    } else {
      const textArea = document.createElement('textarea');
      textArea.value = text;
      textArea.style.position = 'fixed';
      textArea.style.opacity = 0;
      document.body.appendChild(textArea);
      textArea.select();
      document.execCommand('copy');
      document.body.removeChild(textArea);
      
      // Track copy action (fallback)
      if (window.analytics) {
        window.analytics.trackFileCopy('link', 'fallback');
      }
      
      button.textContent = '✅ Đã copy!';
      setTimeout(() => { button.textContent = originalText; }, 2000);
    }
  }

  async function handleExport() {
    const format = document.getElementById('view-export-format').value;
    const widthVal = document.getElementById('view-export-width').value;
    const heightVal = document.getElementById('view-export-height').value;
    const dpiVal = document.getElementById('view-export-dpi').value;
    const msg = document.getElementById('view-export-msg');
    const exportBtn = document.getElementById('view-export-btn');

    msg.textContent = '';
    if ((widthVal && widthVal <= 0) || (heightVal && heightVal <= 0) || (dpiVal && dpiVal <= 0)) {
      msg.textContent = 'Width, Height, DPI phải là số dương!';
      return;
    }

    exportBtn.disabled = true;
    exportBtn.textContent = 'Đang xử lý...';
    try {
      const filename = window.location.pathname.split('/').pop();
      const res = await fetch('/convert', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          filename: filename,
          fmt: format,
          width: widthVal || undefined,
          height: heightVal || undefined,
          dpi: dpiVal || undefined
        })
      });
      const data = await res.json();
      if (data.url) {
        // Track successful export
        if (window.analytics) {
          if (format === 'svg') {
            window.analytics.trackFileDownload('svg', data.filename || 'exported.svg');
          } else {
            window.analytics.trackImageExport(format, data.actual_size || `${widthVal || 'auto'}x${heightVal || 'auto'}`);
          }
        }
        
        let fileInfoText = '';
        if (data.file_size) {
          const sizeKB = (data.file_size / 1024).toFixed(1);
          fileInfoText = `<div class="small-info">Dung lượng: ${sizeKB} KB${data.actual_size ? ` | Kích thước: ${data.actual_size}` : ''}</div>`;
        }
        msg.className = '';
        msg.innerHTML = `<a href="${data.url}" download class="export-download-link">Tải về ${format.toUpperCase()}</a>${fileInfoText}`;
      } else {
        // Track export error
        if (window.analytics) {
          window.analytics.trackUserAction('export_error', {
            'format': format,
            'error_type': 'server_error',
            'error_message': data.error || 'unknown_error',
            'page': 'view_svg'
          });
        }
        
        msg.className = 'error';
        msg.textContent = data.error || 'Lỗi không xác định!';
        if (data.estimated_size_mb) {
          const small = document.createElement('small');
          small.className = 'small-info';
          small.textContent = `Dung lượng ước tính: ${data.estimated_size_mb}`;
          msg.appendChild(document.createElement('br'));
          msg.appendChild(small);
        }
        if (data.note) {
          const small2 = document.createElement('small');
          small2.className = 'small-info';
          small2.textContent = data.note;
          msg.appendChild(document.createElement('br'));
          msg.appendChild(small2);
        }
      }
    } catch (err) {
      // Track network error
      if (window.analytics) {
        window.analytics.trackUserAction('export_error', {
          'format': format,
          'error_type': 'network_error',
          'error_message': err.message || 'connection_error',
          'page': 'view_svg'
        });
      }
      
      msg.className = 'error';
      msg.textContent = 'Lỗi kết nối hoặc máy chủ!';
    }
    exportBtn.disabled = false;
    exportBtn.textContent = 'Tải xuống';
  }

  document.addEventListener('DOMContentLoaded', function() {
    // Logout open
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', function() {
        const modal = document.getElementById('logout-modal');
        if (modal) modal.style.display = 'flex';
      });
    }

    // Mobile logout button
    const mobileLogoutBtn = document.getElementById('mobile-logout-btn');
    if (mobileLogoutBtn) {
      mobileLogoutBtn.addEventListener('click', function() {
        const modal = document.getElementById('logout-modal');
        if (modal) modal.style.display = 'flex';
      });
    }

    // Close modals (cancel buttons)
    const logoutCancel = document.querySelector('#logout-modal .btn-secondary');
    if (logoutCancel) {
      logoutCancel.addEventListener('click', function() {
        document.getElementById('logout-modal').style.display = 'none';
      });
    }
    const loginCancel = document.querySelector('#login-modal .btn-cancel');
    if (loginCancel) {
      loginCancel.addEventListener('click', function() {
        document.getElementById('login-modal').style.display = 'none';
      });
    }

    // Mobile dark mode toggle mirrors desktop toggle
    const mobileDarkModeToggle = document.getElementById('mobile-dark-mode-toggle');
    if (mobileDarkModeToggle) {
      mobileDarkModeToggle.addEventListener('click', function() {
        const desktopToggle = document.getElementById('dark-mode-toggle');
        if (desktopToggle) desktopToggle.click();
      });
    }

    // Mobile 2-tap functionality
    const mobileNavItems = document.querySelectorAll('.mobile-nav-item');
    let activeTooltip = null;
    mobileNavItems.forEach(item => {
      const tooltip = item.querySelector('.mobile-nav-tooltip');
      const action = item.getAttribute('data-action');
      item.addEventListener('click', function(e) {
        e.preventDefault();
        if (activeTooltip && activeTooltip !== tooltip) {
          activeTooltip.classList.remove('active');
        }
        tooltip.classList.toggle('active');
        activeTooltip = tooltip.classList.contains('active') ? tooltip : null;
      });
      tooltip.addEventListener('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        switch(action) {
          case 'home':
            window.location.href = '/';
            break;
          case 'dark-mode':
            const desktopToggle = document.getElementById('dark-mode-toggle');
            if (desktopToggle) desktopToggle.click();
            break;
          case 'profile':
            window.location.href = '/profile/me';
            break;
          case 'logout':
            document.getElementById('logout-modal').style.display = 'flex';
            break;
          case 'login':
            const currentUrl = window.location.pathname + window.location.search;
            const setNextUrl = document.body.getAttribute('data-set-next-url');
            window.location.href = `${setNextUrl}?url=${encodeURIComponent(currentUrl)}`;
            break;
        }
        tooltip.classList.remove('active');
        activeTooltip = null;
      });
    });
    document.addEventListener('click', function(e) {
      if (!e.target.closest('.mobile-nav-item')) {
        if (activeTooltip) {
          activeTooltip.classList.remove('active');
          activeTooltip = null;
        }
      }
    });

    // Google login button in modal
    const modalLoginBtn = document.getElementById('modal-login-btn');
    if (modalLoginBtn) {
      modalLoginBtn.addEventListener('click', function(e) {
        e.preventDefault();
        const currentUrl = window.location.pathname + window.location.search;
        const setNextUrl = document.body.getAttribute('data-set-next-url');
        window.location.href = `${setNextUrl}?url=${encodeURIComponent(currentUrl)}`;
      });
    }

    // Copy link
    const copyLinkBtn = document.getElementById('view-copy-link-btn');
    if (copyLinkBtn) {
      copyLinkBtn.addEventListener('click', function() {
        const svgPath = document.getElementById('view-svg-img').getAttribute('src');
        const baseUrl = window.location.origin;
        const fullSvgUrl = baseUrl + svgPath;
        copyToClipboard(fullSvgUrl, this, '🔗 Copy Link');
      });
    }

    // Download SVG
    const downloadSvgBtn = document.getElementById('view-download-svg-btn');
    if (downloadSvgBtn) {
      downloadSvgBtn.addEventListener('click', function() {
        requireLogin(() => {
          // Track SVG download
          if (window.analytics) {
            window.analytics.trackFileDownload('svg', 'direct_download.svg');
          }
          
          const svgUrl = document.getElementById('view-svg-img').getAttribute('src');
          const link = document.createElement('a');
          link.href = svgUrl;
          link.download = '';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        });
      });
    }

    // Back to edit button
    const backToEditBtn = document.getElementById('view-back-to-edit-btn');
    if (backToEditBtn) {
      backToEditBtn.addEventListener('click', function() {
        requireLogin(() => {
          const tikzJsonEl = document.getElementById('tikz-code-json');
          const tikzCode = tikzJsonEl ? JSON.parse(tikzJsonEl.textContent) : '';
          let currentCode = window.currentViewTikzCode
                          || localStorage.getItem('tikz_code_for_edit')
                          || tikzCode;
          localStorage.setItem('tikz_code_for_compile', currentCode);
          window.location.href = '/';
        });
      });
    }

    // Export
    const exportBtn = document.getElementById('view-export-btn');
    if (exportBtn) {
      exportBtn.addEventListener('click', function() {
        requireLogin(function() {
          handleExport();
        });
      });
    }

    // After login param cleanup
    if (window.location.search.includes('login=1')) {
      const url = new URL(window.location);
      url.searchParams.delete('login');
      window.location.href = url.pathname + url.search;
    }

    // Mobile menu toggle
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenu = document.getElementById('close-menu');
    if (menuToggle && mobileMenu && closeMenu) {
      menuToggle.addEventListener('click', () => mobileMenu.classList.remove('hidden'));
      closeMenu.addEventListener('click', () => mobileMenu.classList.add('hidden'));
      mobileMenu.addEventListener('click', e => { if (e.target === mobileMenu) mobileMenu.classList.add('hidden'); });
    }

    // Initialize highlight.js if available
    if (window.hljs && typeof window.hljs.highlightAll === 'function') {
      window.hljs.highlightAll();
      if (window.hljs.initLineNumbersOnLoad) window.hljs.initLineNumbersOnLoad();
    }

    // Initialize Caption Feature
    initCaptionFeature();
  });

  // ===== CAPTION MANAGEMENT =====
  
  function initCaptionFeature() {
    const captionData = getCaptionData();
    if (!captionData) return;
    
    const editBtn = document.getElementById('edit-caption-btn');
    const saveBtn = document.getElementById('save-caption-btn');
    const cancelBtn = document.getElementById('cancel-caption-btn');
    const captionInput = document.getElementById('caption-input');
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const charCurrent = document.getElementById('caption-char-current');
    const previewContent = document.getElementById('caption-preview-content');
    
    // Render MathJax for initial caption display (for both owner and non-owner)
    if (captionData.caption && captionData.caption.trim()) {
      const captionText = document.querySelector('.caption-text');
      if (captionText && captionText.textContent.trim()) {
        // Wait for MathJax to be ready
        if (window.MathJax && window.MathJax.typesetPromise) {
          window.MathJax.typesetPromise([captionText]).catch(err => {
            console.error('MathJax typeset error:', err);
          });
        } else {
          // MathJax not ready yet, wait a bit
          setTimeout(() => {
            if (window.MathJax && window.MathJax.typesetPromise) {
              window.MathJax.typesetPromise([captionText]).catch(err => {
                console.error('MathJax typeset error:', err);
              });
            }
          }, 500);
        }
      }
    }
    
    // If not owner, only render MathJax and return
    if (!captionData.isOwner) {
      return;
    }
    
    // Edit button click
    if (editBtn) {
      console.log('Edit button found, adding click listener');
      editBtn.addEventListener('click', function(e) {
        console.log('Edit button clicked!', e);
        enableCaptionEdit();
      });
    } else {
      console.log('Edit button NOT found!');
    }
    
    // Save button click
    if (saveBtn) {
      saveBtn.addEventListener('click', function() {
        saveCaptionHandler();
      });
    }
    
    // Cancel button click
    if (cancelBtn) {
      cancelBtn.addEventListener('click', function() {
        cancelCaptionEdit();
      });
    }
    
    // Character counter and preview
    if (captionInput && charCurrent) {
      captionInput.addEventListener('input', function() {
        const length = this.value.length;
        charCurrent.textContent = length;
        
        // Update preview
        if (previewContent) {
          const text = this.value || '(Preview sẽ hiển thị ở đây)';
          // Convert line breaks to <br> tags for preview
          // Use textContent first to escape HTML, then replace \n with <br>
          const tempDiv = document.createElement('div');
          tempDiv.textContent = text;
          const escapedText = tempDiv.innerHTML;
          previewContent.innerHTML = escapedText.replace(/\n/g, '<br>');
          
          if (window.MathJax) {
            window.MathJax.typesetPromise([previewContent]).catch(err => {
              console.error('MathJax typeset error:', err);
            });
          }
        }
      });
    }
  }
  
  function getCaptionData() {
    const dataEl = document.getElementById('caption-data-json');
    if (!dataEl) return null;
    try {
      return JSON.parse(dataEl.textContent);
    } catch (e) {
      console.error('Error parsing caption data:', e);
      return null;
    }
  }
  
  function enableCaptionEdit() {
    console.log('enableCaptionEdit called');
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const editBtn = document.getElementById('edit-caption-btn');
    
    console.log('Elements found:', {
      captionDisplay: !!captionDisplay,
      captionEmpty: !!captionEmpty,
      captionEditForm: !!captionEditForm,
      editBtn: !!editBtn
    });
    
    if (captionDisplay) captionDisplay.style.display = 'none';
    if (captionEmpty) captionEmpty.style.display = 'none';
    if (captionEditForm) captionEditForm.style.display = 'block';
    if (editBtn) editBtn.style.display = 'none';
    
    // Focus on textarea
    const captionInput = document.getElementById('caption-input');
    if (captionInput) {
      captionInput.focus();
      
      // Initialize preview
      const previewContent = document.getElementById('caption-preview-content');
      if (previewContent) {
        const text = captionInput.value || '(Preview sẽ hiển thị ở đây)';
        // Convert line breaks to <br> tags for preview
        const tempDiv = document.createElement('div');
        tempDiv.textContent = text;
        const escapedText = tempDiv.innerHTML;
        previewContent.innerHTML = escapedText.replace(/\n/g, '<br>');
        
        if (window.MathJax) {
          window.MathJax.typesetPromise([previewContent]).catch(err => {
            console.error('MathJax typeset error:', err);
          });
        }
      }
    }
  }
  
  function cancelCaptionEdit() {
    const captionData = getCaptionData();
    const captionDisplay = document.getElementById('caption-display');
    const captionEmpty = document.getElementById('caption-empty');
    const captionEditForm = document.getElementById('caption-edit-form');
    const editBtn = document.getElementById('edit-caption-btn');
    const captionInput = document.getElementById('caption-input');
    
    // Reset form to original value
    if (captionInput && captionData) {
      captionInput.value = captionData.caption || '';
      const charCurrent = document.getElementById('caption-char-current');
      if (charCurrent) {
        charCurrent.textContent = captionInput.value.length;
      }
    }
    
    // Hide edit form, show edit button
    if (captionEditForm) captionEditForm.style.display = 'none';
    if (editBtn) editBtn.style.display = 'flex';
    
    // Show appropriate display mode based on whether caption exists
    if (captionData && captionData.caption && captionData.caption.trim()) {
      // Has caption - show display, hide empty
      if (captionDisplay) captionDisplay.style.display = 'block';
      if (captionEmpty) captionEmpty.style.display = 'none';
    } else {
      // No caption - hide display, show empty
      if (captionDisplay) captionDisplay.style.display = 'none';
      if (captionEmpty) captionEmpty.style.display = 'block';
    }
    
    hideMessage();
  }
  
  async function saveCaptionHandler() {
    const captionData = getCaptionData();
    if (!captionData) return;
    
    const captionInput = document.getElementById('caption-input');
    const saveBtn = document.getElementById('save-caption-btn');
    
    if (!captionInput || !saveBtn) return;
    
    const newCaption = captionInput.value.trim();
    
    // Disable button
    saveBtn.disabled = true;
    saveBtn.innerHTML = '⏳ Đang lưu...';
    
    try {
      const response = await fetch(`/api/update_caption/${captionData.filename}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ caption: newCaption })
      });
      
      const result = await response.json();
      
      if (result.success) {
        // Update caption data first
        captionData.caption = newCaption;
        
        // Update display elements
        const captionText = document.querySelector('.caption-text');
        const captionDisplay = document.getElementById('caption-display');
        const captionEmpty = document.getElementById('caption-empty');
        const captionEditForm = document.getElementById('caption-edit-form');
        const editBtn = document.getElementById('edit-caption-btn');
        
        // Update caption text content
        if (captionText) {
          // Convert line breaks to <br> tags for display
          const tempDiv = document.createElement('div');
          tempDiv.textContent = newCaption;
          const escapedText = tempDiv.innerHTML;
          captionText.innerHTML = escapedText.replace(/\n/g, '<br>');
          
          // Trigger MathJax rendering
          if (window.MathJax) {
            window.MathJax.typesetPromise([captionText]).catch(err => {
              console.error('MathJax typeset error:', err);
            });
          }
        }
        
        // Update edit button text
        if (editBtn) {
          const editText = editBtn.querySelector('.edit-text');
          if (editText) {
            editText.textContent = newCaption ? 'Chỉnh sửa mô tả' : 'Thêm mô tả';
          }
        }
        
        // Hide edit form
        if (captionEditForm) captionEditForm.style.display = 'none';
        if (editBtn) editBtn.style.display = 'flex';
        
        // Show appropriate display mode
        if (newCaption && newCaption.trim()) {
          // Has caption - show display, hide empty
          if (captionDisplay) captionDisplay.style.display = 'block';
          if (captionEmpty) captionEmpty.style.display = 'none';
        } else {
          // No caption - hide display, show empty
          if (captionDisplay) captionDisplay.style.display = 'none';
          if (captionEmpty) captionEmpty.style.display = 'block';
        }
        
        // Show success message
        showMessage(result.message, 'success');
      } else {
        showMessage(result.error || 'Có lỗi xảy ra', 'error');
      }
    } catch (error) {
      console.error('Error saving caption:', error);
      showMessage('Lỗi kết nối. Vui lòng thử lại.', 'error');
    } finally {
      // Re-enable button
      saveBtn.disabled = false;
      saveBtn.innerHTML = '✅ Lưu';
    }
  }
  
  function showMessage(text, type = 'success') {
    const messageEl = document.getElementById('caption-message');
    if (!messageEl) return;
    
    messageEl.textContent = text;
    messageEl.className = 'caption-message ' + type;
    
    // Auto hide after 5 seconds
    setTimeout(() => {
      hideMessage();
    }, 5000);
  }
  
  function hideMessage() {
    const messageEl = document.getElementById('caption-message');
    if (messageEl) {
      messageEl.style.display = 'none';
      messageEl.className = 'caption-message';
    }
  }
  
})();


