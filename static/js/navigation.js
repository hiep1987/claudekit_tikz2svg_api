;(function() {
"use strict";

// ===== NAVIGATION COMPONENT =====

// Initialize navigation component
function initializeNavigationComponent() {
    // Initialize mobile menu
    initializeMobileMenu();
    
    // Initialize logout functionality
    initializeLogoutHandler();
    
    console.log('🔄 Navigation component initialized');
}

// ===== MOBILE MENU FUNCTIONALITY =====

// Initialize mobile menu toggle functionality
function initializeMobileMenu() {
    const menuToggle = document.getElementById('menu-toggle');
    const mobileMenu = document.getElementById('mobile-menu');
    const closeMenu = document.getElementById('close-menu');
    
    if (menuToggle && mobileMenu && closeMenu) {
        // Toggle menu open
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.remove('hidden');
        });
        
        // Close menu with close button
        closeMenu.addEventListener('click', () => {
            mobileMenu.classList.add('hidden');
        });
        
        // Close menu when clicking outside
        mobileMenu.addEventListener('click', e => { 
            if (e.target === mobileMenu) {
                mobileMenu.classList.add('hidden');
            }
        });
        
        console.log('🔄 Mobile menu initialized');
    }
}

// ===== LOGOUT FUNCTIONALITY =====

// Initialize logout link handler
function initializeLogoutHandler() {
    const logoutLink = document.getElementById('logout-link');
    if (logoutLink) {
        logoutLink.addEventListener('click', function(e) {
            e.preventDefault();
            window.location.href = '/logout?next=/';
        });
        console.log('🔄 Logout handler initialized');
    }
}

// ===== HEADER LOGIN STATE MANAGEMENT =====

// Update header login state (basic version - can be extended)
function updateHeaderLoginState() {
    // Basic header state management
    // This function can be extended based on specific needs
    
    if (window.appState && window.appState.loggedIn) {
        console.log('🔄 Header login state updated - User logged in');
        // Add any specific header logic here
    } else {
        console.log('🔄 Header login state updated - User not logged in');
        // Add any specific header logic here
    }
}

// ===== EXPOSE MODULE =====

// Expose navigation component initializer
window.NavigationComponent = {
    init: initializeNavigationComponent,
    updateHeaderLoginState: updateHeaderLoginState
};

})();
