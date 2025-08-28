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
        let fileInfoText = '';
        if (data.file_size) {
          const sizeKB = (data.file_size / 1024).toFixed(1);
          fileInfoText = `<div class="small-info">Dung lượng: ${sizeKB} KB${data.actual_size ? ` | Kích thước: ${data.actual_size}` : ''}</div>`;
        }
        msg.className = '';
        msg.innerHTML = `<a href="${data.url}" download class="export-download-link">Tải về ${format.toUpperCase()}</a>${fileInfoText}`;
      } else {
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
  });
})();


