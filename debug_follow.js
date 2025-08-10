// Debug script for follow/unfollow functionality

function debugFollow(userId) {
    console.log('🔍 Debugging follow function...');
    console.log('User ID:', userId);
    
    // Test 1: Check if button exists
    const followBtn = document.querySelector(`.follow-btn[data-user-id="${userId}"]`);
    console.log('Follow button found:', followBtn);
    
    // Test 2: Check if follower count element exists
    const spans = document.querySelectorAll('.public-profile-header span');
    let followerCountElement = null;
    for (let span of spans) {
        if (span.textContent.includes('👥')) {
            followerCountElement = span;
            break;
        }
    }
    console.log('Follower count element found:', followerCountElement);
    if (followerCountElement) {
        console.log('Current follower count text:', followerCountElement.textContent);
    }
    
    // Test 3: Simulate API call
    console.log('🔍 Simulating API call to /follow/' + userId);
    
    fetch(`/follow/${userId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        console.log('Response status:', response.status);
        return response.json();
    })
    .then(data => {
        console.log('Response data:', data);
        
        if (data.success) {
            console.log('✅ API call successful');
            
            // Test button update
            if (followBtn) {
                followBtn.textContent = '👥 Bỏ theo dõi';
                followBtn.className = 'btn btn-secondary follow-btn';
                console.log('✅ Button updated');
            }
            
            // Test follower count update
            if (followerCountElement) {
                const currentText = followerCountElement.textContent;
                const currentCount = parseInt(currentText.match(/\d+/)[0]) || 0;
                followerCountElement.textContent = `👥 ${currentCount + 1} followers`;
                console.log(`✅ Follower count updated from ${currentCount} to ${currentCount + 1}`);
            }
        } else {
            console.log('❌ API call failed:', data.message);
        }
    })
    .catch(error => {
        console.error('❌ Network error:', error);
    });
}

// Add to window for testing
window.debugFollow = debugFollow; 