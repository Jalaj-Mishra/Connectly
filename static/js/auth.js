// Authentication Pages JavaScript
// Handles login and register page interactions

document.addEventListener('DOMContentLoaded', function() {
    // Initialize page animations
    initPageAnimations();
    
    // Initialize form interactions
    initFormInteractions();
    
    // Initialize floating elements animation
    initFloatingElements();
});

/**
 * Initialize page load animations
 */
function initPageAnimations() {
    // Animate social cards on login page
    const socialCards = document.querySelectorAll('.social-card');
    socialCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 200);
    });

    // Animate metric cards on register page
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // Animate form container
    const formContainer = document.querySelector('.form-container');
    if (formContainer) {
        formContainer.style.opacity = '0';
        formContainer.style.transform = 'translateX(20px)';
        setTimeout(() => {
            formContainer.style.transition = 'all 0.6s ease';
            formContainer.style.opacity = '1';
            formContainer.style.transform = 'translateX(0)';
        }, 300);
    }
}

/**
 * Toggle password visibility
 * @param {string} fieldName - Name of the password field
 */
function togglePassword(fieldName) {
    const passwordInput = document.querySelector(`input[name="${fieldName}"]`);
    const toggleIcon = passwordInput.parentElement.querySelector('.password-toggle');
    
    if (passwordInput && toggleIcon) {
        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleIcon.classList.remove('fa-eye');
            toggleIcon.classList.add('fa-eye-slash');
            toggleIcon.title = 'Hide password';
        } else {
            passwordInput.type = 'password';
            toggleIcon.classList.remove('fa-eye-slash');
            toggleIcon.classList.add('fa-eye');
            toggleIcon.title = 'Show password';
        }
    }
}

/**
 * Initialize form interactions
 */
function initFormInteractions() {
    // Add focus effects to form inputs
    const formInputs = document.querySelectorAll('.form-group input');
    formInputs.forEach(input => {
        // Add floating label effect
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            if (this.value === '') {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if input has value on page load
        if (input.value !== '') {
            input.parentElement.classList.add('focused');
        }
    });

    // Only add validation to registration forms (forms with password2 field)
    const allForms = document.querySelectorAll('form');
    allForms.forEach(form => {
        const isRegisterForm = form.querySelector('input[name="password2"]') !== null;
        
        if (isRegisterForm) {
            // Registration form - add validation
            form.addEventListener('submit', function(e) {
                if (!validateRegistrationForm(this)) {
                    e.preventDefault();
                }
            });
        }
        // For login forms, do nothing - let them submit naturally
    });

    // Google sign-in button interaction
    const googleBtn = document.querySelector('.google-btn');
    if (googleBtn) {
        googleBtn.addEventListener('click', function() {
            // Add your Google OAuth logic here
            console.log('Google sign-in clicked');
            // For now, just show a message
            showNotification('Google sign-in feature coming soon!', 'info');
        });
    }
}

/**
 * Validate registration form before submission
 * @param {HTMLFormElement} form - The registration form to validate
 * @returns {boolean} - Whether the form is valid
 */
function validateRegistrationForm(form) {
    let isValid = true;
    
    // For registration forms, use comprehensive validation
    const inputs = form.querySelectorAll('input[required], input[name="username"], input[name="password1"], input[name="password2"]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            showFieldError(input, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(input);
        }
        
        // Email validation
        if (input.type === 'email' && input.value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(input.value)) {
                showFieldError(input, 'Please enter a valid email address');
                isValid = false;
            }
        }
        
        // Password confirmation validation
        if (input.name === 'password2') {
            const password1 = form.querySelector('input[name="password1"]');
            if (password1 && input.value !== password1.value) {
                showFieldError(input, 'Passwords do not match');
                isValid = false;
            }
        }
    });
    
    return isValid;
}

/**
 * Show field error message
 * @param {HTMLInputElement} input - The input field
 * @param {string} message - Error message
 */
function showFieldError(input, message) {
    clearFieldError(input);
    
    input.style.borderColor = '#ef4444';
    input.style.background = '#fef2f2';
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'field-error';
    errorDiv.style.cssText = `
        color: #ef4444;
        font-size: 0.8rem;
        margin-top: 0.25rem;
        display: flex;
        align-items: center;
        gap: 0.25rem;
    `;
    errorDiv.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
    
    input.parentElement.appendChild(errorDiv);
}

/**
 * Clear field error message
 * @param {HTMLInputElement} input - The input field
 */
function clearFieldError(input) {
    input.style.borderColor = '';
    input.style.background = '';
    
    const existingError = input.parentElement.querySelector('.field-error');
    if (existingError) {
        existingError.remove();
    }
}

/**
 * Add loading state to button
 * @param {HTMLButtonElement} button - The button element
 */
function addLoadingState(button) {
    const originalText = button.innerHTML;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    button.disabled = true;
    
    // Remove loading state after 3 seconds (adjust as needed)
    setTimeout(() => {
        button.innerHTML = originalText;
        button.disabled = false;
    }, 3000);
}

/**
 * Show notification message
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, info)
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        border-radius: 8px;
        color: white;
        font-weight: 500;
        z-index: 1000;
        animation: slideIn 0.3s ease;
        max-width: 300px;
    `;
    
    // Set background color based on type
    switch(type) {
        case 'success':
            notification.style.background = '#10b981';
            break;
        case 'error':
            notification.style.background = '#ef4444';
            break;
        default:
            notification.style.background = '#3b82f6';
    }
    
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 0.5rem;">
            <i class="fas fa-${type === 'success' ? 'check' : type === 'error' ? 'times' : 'info'}-circle"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Remove notification after 3 seconds
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            if (notification.parentElement) {
                notification.parentElement.removeChild(notification);
            }
        }, 300);
    }, 3000);
}

/**
 * Initialize floating elements animation
 */
function initFloatingElements() {
    const floatingElements = document.querySelectorAll('.floating-element');
    floatingElements.forEach((element, index) => {
        // Add random delay to make animation more organic
        const delay = Math.random() * 2;
        element.style.animationDelay = `${delay}s`;
        
        // Add random animation duration for variety
        const duration = 6 + Math.random() * 4; // 6-10 seconds
        element.style.animationDuration = `${duration}s`;
    });
}

/**
 * Initialize parallax effect for floating elements
 */
function initParallaxEffect() {
    const leftSide = document.querySelector('.left-side');
    const floatingElements = document.querySelectorAll('.floating-element');
    
    if (leftSide && floatingElements.length > 0) {
        leftSide.addEventListener('mousemove', function(e) {
            const { clientX, clientY } = e;
            const { offsetWidth, offsetHeight } = this;
            
            const xPercent = (clientX / offsetWidth - 0.5) * 2;
            const yPercent = (clientY / offsetHeight - 0.5) * 2;
            
            floatingElements.forEach((element, index) => {
                const speed = (index + 1) * 0.5;
                const x = xPercent * speed;
                const y = yPercent * speed;
                
                element.style.transform = `translate(${x}px, ${y}px)`;
            });
        });
        
        leftSide.addEventListener('mouseleave', function() {
            floatingElements.forEach(element => {
                element.style.transform = 'translate(0, 0)';
            });
        });
    }
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
    
    .form-group.focused input {
        border-color: #667eea;
        background: white;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .floating-element {
        transition: transform 0.3s ease;
    }
`;
document.head.appendChild(style);

// Initialize parallax effect after DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setTimeout(initParallaxEffect, 500);
});

// Export functions for global use
window.togglePassword = togglePassword;
