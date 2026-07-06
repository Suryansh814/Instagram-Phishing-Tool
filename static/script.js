document.addEventListener('DOMContentLoaded', function() {
    const loginForm = document.querySelector('.login-form');
    const usernameInput = document.querySelector('input[name="username"]');
    const passwordInput = document.querySelector('input[name="password"]');
    const loginButton = document.querySelector('.login-button');
    
    // Enable/disable login button based on form inputs
    function checkFormValidity() {
        if (usernameInput.value.trim() && passwordInput.value.trim()) {
            loginButton.disabled = false;
        } else {
            loginButton.disabled = true;
        }
    }
    
    usernameInput.addEventListener('input', checkFormValidity);
    passwordInput.addEventListener('input', checkFormValidity);
    
    // Handle form submission
    loginForm.addEventListener('submit', function(e) {
        // Disable button to prevent multiple submissions
        loginButton.disabled = true;
        loginButton.textContent = 'Logging in...';
        
        // Form will be submitted normally
    });
    
    // Facebook login button (for looks only)
    const facebookLogin = document.querySelector('.facebook-login');
    facebookLogin.addEventListener('click', function() {
        alert('This feature is not available in this demo');
    });
    
    // Forgot password link
    const forgotPassword = document.querySelector('.forgot-password');
    forgotPassword.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Please contact Instagram support for password recovery');
    });
    
    // Sign up link
    const signUpLink = document.querySelector('.signup-box a');
    signUpLink.addEventListener('click', function(e) {
        e.preventDefault();
        alert('Please visit Instagram.com to create a new account');
    });
});
