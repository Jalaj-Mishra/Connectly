/* Common JavaScript Utilities for Social Dashboard */

// Utility Functions
const Utils = {
    // Debounce function for performance optimization
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                timeout = null;
                if (!immediate) func.apply(this, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(this, args);
        };
    },

    // Throttle function for performance optimization
    throttle: function(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    },

    // Format numbers with commas
    formatNumber: function(num) {
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    },

    // Format date to relative time
    formatDate: function(date) {
        const now = new Date();
        const diffTime = Math.abs(now - new Date(date));
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        
        if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return `${diffDays} days ago`;
        } else if (diffDays < 30) {
            return `${Math.ceil(diffDays / 7)} weeks ago`;
        } else {
            return `${Math.ceil(diffDays / 30)} months ago`;
        }
    },

    // Show toast notifications
    showToast: function(message, type = 'info', duration = 3000) {
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.innerHTML = `
            <div class="toast-content">
                <span class="toast-message">${message}</span>
                <button class="toast-close" onclick="this.parentElement.parentElement.remove()">×</button>
            </div>
        `;
        
        // Add toast styles if not already present
        if (!document.querySelector('#toast-styles')) {
            const styles = document.createElement('style');
            styles.id = 'toast-styles';
            styles.textContent = `
                .toast {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    min-width: 300px;
                    padding: 1rem;
                    border-radius: 10px;
                    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                    z-index: 10000;
                    animation: slideInRight 0.3s ease;
                }
                .toast-info { background: #3b82f6; color: white; }
                .toast-success { background: #10b981; color: white; }
                .toast-warning { background: #f59e0b; color: white; }
                .toast-error { background: #ef4444; color: white; }
                .toast-content {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    gap: 1rem;
                }
                .toast-close {
                    background: none;
                    border: none;
                    color: inherit;
                    font-size: 1.2rem;
                    cursor: pointer;
                    padding: 0;
                    margin: 0;
                }
                @keyframes slideInRight {
                    from { transform: translateX(100%); opacity: 0; }
                    to { transform: translateX(0); opacity: 1; }
                }
            `;
            document.head.appendChild(styles);
        }
        
        document.body.appendChild(toast);
        
        // Auto remove after duration
        setTimeout(() => {
            if (toast.parentElement) {
                toast.style.animation = 'slideInRight 0.3s ease reverse';
                setTimeout(() => toast.remove(), 300);
            }
        }, duration);
    },

    // Copy text to clipboard
    copyToClipboard: function(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copied to clipboard!', 'success');
        }).catch(() => {
            this.showToast('Failed to copy to clipboard', 'error');
        });
    },

    // Check if element is in viewport
    isInViewport: function(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }
};

// Form Validation Utilities
const FormValidator = {
    // Email validation
    isValidEmail: function(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    // Password strength validation
    validatePassword: function(password) {
        const minLength = 8;
        const hasUpperCase = /[A-Z]/.test(password);
        const hasLowerCase = /[a-z]/.test(password);
        const hasNumbers = /\d/.test(password);
        const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(password);

        return {
            isValid: password.length >= minLength && hasUpperCase && hasLowerCase && hasNumbers,
            strength: this.getPasswordStrength(password),
            requirements: {
                minLength: password.length >= minLength,
                hasUpperCase,
                hasLowerCase,
                hasNumbers,
                hasSpecialChar
            }
        };
    },

    // Get password strength score
    getPasswordStrength: function(password) {
        let score = 0;
        if (password.length >= 8) score++;
        if (password.length >= 12) score++;
        if (/[A-Z]/.test(password)) score++;
        if (/[a-z]/.test(password)) score++;
        if (/\d/.test(password)) score++;
        if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score++;
        
        if (score < 3) return 'weak';
        if (score < 5) return 'medium';
        return 'strong';
    },

    // Add validation feedback to form field
    showFieldError: function(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('error');
        const errorEl = document.createElement('div');
        errorEl.className = 'field-error';
        errorEl.textContent = message;
        errorEl.style.cssText = `
            color: #ef4444;
            font-size: 0.8rem;
            margin-top: 0.25rem;
            animation: fadeIn 0.3s ease;
        `;
        
        field.parentNode.appendChild(errorEl);
    },

    // Clear field error
    clearFieldError: function(field) {
        field.classList.remove('error');
        const errorEl = field.parentNode.querySelector('.field-error');
        if (errorEl) {
            errorEl.remove();
        }
    }
};

// Animation Utilities
const AnimationUtils = {
    // Fade in animation
    fadeIn: function(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let opacity = 0;
        const timer = setInterval(() => {
            opacity += 50 / duration;
            if (opacity >= 1) {
                clearInterval(timer);
                opacity = 1;
            }
            element.style.opacity = opacity;
        }, 50);
    },

    // Fade out animation
    fadeOut: function(element, duration = 300) {
        let opacity = 1;
        const timer = setInterval(() => {
            opacity -= 50 / duration;
            if (opacity <= 0) {
                clearInterval(timer);
                element.style.display = 'none';
                opacity = 0;
            }
            element.style.opacity = opacity;
        }, 50);
    },

    // Slide down animation
    slideDown: function(element, duration = 300) {
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        let height = 0;
        const increment = targetHeight / (duration / 10);
        
        const timer = setInterval(() => {
            height += increment;
            if (height >= targetHeight) {
                clearInterval(timer);
                element.style.height = 'auto';
                element.style.overflow = 'visible';
            } else {
                element.style.height = height + 'px';
            }
        }, 10);
    },

    // Slide up animation
    slideUp: function(element, duration = 300) {
        let height = element.scrollHeight;
        const decrement = height / (duration / 10);
        
        const timer = setInterval(() => {
            height -= decrement;
            if (height <= 0) {
                clearInterval(timer);
                element.style.display = 'none';
                element.style.height = 'auto';
            } else {
                element.style.height = height + 'px';
            }
        }, 10);
    }
};

// Loading States
const LoadingManager = {
    // Show loading spinner on button
    showButtonLoading: function(button, loadingText = 'Loading...') {
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner"></span>
            ${loadingText}
        `;
    },

    // Hide loading spinner on button
    hideButtonLoading: function(button) {
        button.disabled = false;
        button.innerHTML = button.dataset.originalText || button.innerHTML;
        delete button.dataset.originalText;
    },

    // Show page loading overlay
    showPageLoading: function() {
        if (document.querySelector('#page-loading')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'page-loading';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <p>Loading...</p>
            </div>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(255, 255, 255, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        document.body.appendChild(overlay);
    },

    // Hide page loading overlay
    hidePageLoading: function() {
        const overlay = document.querySelector('#page-loading');
        if (overlay) {
            overlay.remove();
        }
    }
};

// DOM Ready and Initialization
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        element.addEventListener('mouseenter', function(e) {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = this.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: #1e293b;
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 6px;
                font-size: 0.8rem;
                white-space: nowrap;
                z-index: 1000;
                pointer-events: none;
                top: ${e.pageY - 40}px;
                left: ${e.pageX - 20}px;
                animation: fadeIn 0.2s ease;
            `;
            document.body.appendChild(tooltip);
            
            this.addEventListener('mouseleave', function() {
                tooltip.remove();
            }, { once: true });
        });
    });

    // Initialize smooth scrolling for anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
            }
        });
    });

    // Initialize auto-resize textareas
    const textareas = document.querySelectorAll('textarea[data-auto-resize]');
    textareas.forEach(textarea => {
        const resize = () => {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        };
        
        textarea.addEventListener('input', resize);
        resize(); // Initial resize
    });

    // Initialize copy buttons
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const text = this.dataset.copy;
            Utils.copyToClipboard(text);
        });
    });
});

// Export utilities for use in other files
window.Utils = Utils;
window.FormValidator = FormValidator;
window.AnimationUtils = AnimationUtils;
window.LoadingManager = LoadingManager;
