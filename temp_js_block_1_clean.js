// Store environment detection globally for helper functions
window._gaEnvironment = {
    isDevelopment: window.location.hostname === 'localhost' ||
                  window.location.hostname === '127.0.0.1' ||
                  window.location.port === '5173' ||
                  window.location.port === '5000' ||
                  window.location.hostname.includes('localhost'),
    isProduction: window.location.hostname === 'tikz2svg.com' ||
                 window.location.hostname === 'www.tikz2svg.com'
};

// Set current user ID for frontend use (template syntax removed)
window.currentUserId = null; // This will be set by Jinja2 template
