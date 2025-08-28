// Profile Verification Page JavaScript
// Using Module Pattern to avoid global scope pollution

(function() {
    'use strict';

    // Private functions
    function cancelVerification() {
        if (confirm('Bạn có chắc muốn hủy bỏ quá trình xác thực?')) {
            // Gửi request hủy bỏ xác thực
            fetch(window.location.href, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'cancel_verification=1'
            }).then(response => {
                if (response.ok) {
                    // Redirect về trang profile settings
                    window.location.href = document.querySelector('a[href*="/profile/"][href*="/settings"]').href;
                }
            }).catch(error => {
                console.error('Error canceling verification:', error);
                alert('Có lỗi xảy ra khi hủy bỏ xác thực. Vui lòng thử lại.');
            });
        }
    }

    function showVerificationForm() {
        document.getElementById('verification-form').classList.remove('verification-form-hidden');
        document.getElementById('agreement-section').classList.add('agreement-section-hidden');
        document.getElementById('verification_code').focus();
    }

    function setupMobileMenu() {
        const menuToggle = document.getElementById('menu-toggle');
        const mobileMenu = document.getElementById('mobile-menu');
        const closeMenu = document.getElementById('close-menu');
        
        if (menuToggle && mobileMenu && closeMenu) {
            menuToggle.addEventListener('click', () => mobileMenu.classList.remove('hidden'));
            closeMenu.addEventListener('click', () => mobileMenu.classList.add('hidden'));
            // Optional: click outside to close
            mobileMenu.addEventListener('click', e => {
                if(e.target === mobileMenu) mobileMenu.classList.add('hidden');
            });
        }
    }

    function setupVerificationInput() {
        const verificationInput = document.getElementById('verification_code');
        if (verificationInput) {
            verificationInput.addEventListener('input', function() {
                // Chỉ cho phép nhập số
                this.value = this.value.replace(/[^0-9]/g, '');
            });
        }
    }

    function setupCancelButton() {
        const cancelBtn = document.getElementById('cancel-verification-btn');
        if (cancelBtn) {
            cancelBtn.addEventListener('click', cancelVerification);
        }
    }

    function checkPendingVerification() {
        const hasPendingVerification = document.querySelector('[data-pending-verification="true"]');
        if (hasPendingVerification) {
            showVerificationForm();
        }
    }

    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function () {
        setupMobileMenu();
        setupVerificationInput();
        setupCancelButton();
        checkPendingVerification();
    });

})();
