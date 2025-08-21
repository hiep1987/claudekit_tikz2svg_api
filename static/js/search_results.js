// Global variable for login status from server
// Note: isLoggedIn is set by the server in the HTML template before this script loads

// Initialize like buttons for search results
function initializeSearchResults() {
    // Initialize like buttons if user is logged in
    if (isLoggedIn) {
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
    
    // Initialize touch events for mobile
    if ('ontouchstart' in window || navigator.maxTouchPoints > 0) {
        document.documentElement.classList.add('is-touch');
    }
    
    // Initialize file card functionality
    initializeFileCardActions();
    initializeFileCardTouchEvents();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initializeSearchResults();
    
    // Add login modal event listener
    const loginModal = document.getElementById('login-modal');
    if (loginModal) {
        loginModal.addEventListener('click', function(e) {
            if (e.target === loginModal) {
                loginModal.style.display = 'none';
            }
        });
    }
});
