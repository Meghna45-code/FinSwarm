// ==================== USER AUTH FLOW HANDLERS ====================

function initAuth() {
  const token = localStorage.getItem('finswarm_access_token');
  const storedUser = localStorage.getItem('finswarm_user');
  
  if (token && storedUser) {
    currentUser = storedUser;
    loginSuccess(false);
  } else {
    showAuthForm('signin');
  }
  
  document.getElementById('logout-btn').addEventListener('click', handleLogout);

  // Close profile dropdown when clicking outside
  window.addEventListener('click', (e) => {
    const container = document.querySelector('.profile-dropdown-container');
    const dropdown = document.getElementById('profile-dropdown');
    if (dropdown && !dropdown.classList.contains('hidden') && container && !container.contains(e.target)) {
      dropdown.classList.add('hidden');
    }
  });
}

function showAuthForm(formName) {
  document.querySelectorAll('.auth-form').forEach(form => form.classList.add('hidden'));
  document.getElementById(`form-${formName}`).classList.remove('hidden');
}

async function handleSignInSubmit() {
  const emailInput = document.getElementById('signin-email');
  const passwordInput = document.getElementById('signin-password');
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  
  if (!email || !password) {
    alert("Please enter both email and password.");
    return;
  }
  
  const submitBtn = document.getElementById('btn-submit-signin');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing In...';
  
  try {
    const data = await apiLogin(email, password);
    localStorage.setItem('finswarm_access_token', data.access_token);
    localStorage.setItem('finswarm_user', data.display_name);
    localStorage.setItem('finswarm_email', email);
    if (!localStorage.getItem('finswarm_role')) {
      localStorage.setItem('finswarm_role', 'Market Observer');
    }
    currentUser = data.display_name;
    
    emailInput.value = '';
    passwordInput.value = '';
    loginSuccess(true);
  } catch (err) {
    console.error("Login failed:", err);
    alert(`Login Failed: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

async function handleRegisterSubmit() {
  const nameInput = document.getElementById('register-name');
  const emailInput = document.getElementById('register-email');
  const passwordInput = document.getElementById('register-password');
  const name = nameInput.value.trim();
  const email = emailInput.value.trim();
  const password = passwordInput.value;
  
  if (!name || !email || !password) {
    alert("All fields are required.");
    return;
  }
  if (password.length < 6) {
    alert("Password must be at least 6 characters.");
    return;
  }
  
  const submitBtn = document.getElementById('btn-submit-register');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registering...';
  
  try {
    // 1. Call registration
    await apiRegister(email, name, password);
    
    // 2. Perform auto-login immediately
    const loginData = await apiLogin(email, password);
    localStorage.setItem('finswarm_access_token', loginData.access_token);
    localStorage.setItem('finswarm_user', loginData.display_name);
    localStorage.setItem('finswarm_email', email);
    localStorage.setItem('finswarm_role', 'Market Observer');
    currentUser = loginData.display_name;
    
    nameInput.value = '';
    emailInput.value = '';
    passwordInput.value = '';
    
    // Directly go to the main screen, skipping the tutorial
    loginSuccess(false);
  } catch (err) {
    console.error("Registration failed:", err);
    alert(`Registration Failed: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

async function handleForgotPasswordSubmit() {
  const emailInput = document.getElementById('forgot-email');
  const email = emailInput.value.trim();
  
  if (!email) {
    alert("Please enter your email address.");
    return;
  }
  
  const submitBtn = document.getElementById('btn-submit-forgot');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending PIN...';
  
  try {
    await apiForgotPassword(email);
    alert("If the account exists, a 6-digit password reset PIN has been output to the server console.");
    showAuthForm('verify'); // Transition to Enter PIN view
  } catch (err) {
    console.error("Forgot password request failed:", err);
    alert(`Request Failed: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

async function handleVerifyResetPinSubmit() {
  const emailInput = document.getElementById('forgot-email');
  const pinInput = document.getElementById('reset-pin');
  const email = emailInput.value.trim();
  const pin = pinInput.value.trim();
  
  if (!email) {
    alert("Please enter your email address in the forgot password screen first.");
    showAuthForm('forgot');
    return;
  }
  if (!pin) {
    alert("Please enter the 6-digit PIN.");
    return;
  }
  
  const submitBtn = document.getElementById('btn-submit-verify');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Verifying...';
  
  try {
    await apiVerifyResetPin(email, pin);
    alert("PIN verified successfully! You can now set your new password.");
    showAuthForm('reset'); // Transition to Set New Password view
  } catch (err) {
    console.error("PIN verification failed:", err);
    alert(`Verification Failed: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

async function handleResetPasswordSubmit() {
  const emailInput = document.getElementById('forgot-email');
  const pinInput = document.getElementById('reset-pin');
  const passwordInput = document.getElementById('reset-password');
  
  const email = emailInput.value.trim();
  const pin = pinInput.value.trim();
  const password = passwordInput.value;
  
  if (!email || !pin) {
    alert("Please perform the verification steps first.");
    showAuthForm('forgot');
    return;
  }
  if (!password) {
    alert("Please enter your new password.");
    return;
  }
  if (password.length < 6) {
    alert("Password must be at least 6 characters.");
    return;
  }
  
  const submitBtn = document.getElementById('btn-submit-reset');
  const originalHtml = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Updating...';
  
  try {
    await apiResetPassword(email, pin, password);
    alert("Password reset successfully! Please log in.");
    
    pinInput.value = '';
    passwordInput.value = '';
    emailInput.value = '';
    showAuthForm('signin');
  } catch (err) {
    console.error("Password reset failed:", err);
    alert(`Password Reset Failed: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalHtml;
  }
}

function loginSuccess(showTutorialOnLogin = false) {
  document.getElementById('user-profile-name').textContent = currentUser;
  
  const role = localStorage.getItem('finswarm_role') || 'Market Observer';
  document.getElementById('user-profile-role').textContent = role;
  
  const email = localStorage.getItem('finswarm_email') || '';
  
  const initials = currentUser.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  document.getElementById('user-avatar-initials').textContent = initials;
  document.getElementById('user-avatar-top').textContent = initials;
  
  document.getElementById('dropdown-user-name').textContent = currentUser;
  document.getElementById('dropdown-user-email').textContent = email;
  document.getElementById('dropdown-user-role').textContent = role;
  
  document.getElementById('greeting-title').textContent = `What's new, ${currentUser}?`;
  
  document.getElementById('auth-screen').classList.remove('active');
  
  loadSidebarData();
  
  if (showTutorialOnLogin) {
    document.getElementById('tutorial-screen').classList.add('active');
    showTutorialSlide(0);
  } else {
    document.getElementById('main-screen').classList.add('active');
  }
}

function handleLogout() {
  localStorage.removeItem('finswarm_user');
  localStorage.removeItem('finswarm_access_token');
  localStorage.removeItem('finswarm_email');
  localStorage.removeItem('finswarm_role');
  currentUser = null;
  
  const dropdown = document.getElementById('profile-dropdown');
  if (dropdown) dropdown.classList.add('hidden');
  
  document.getElementById('main-screen').classList.remove('active');
  document.getElementById('auth-screen').classList.add('active');
  showAuthForm('signin');
}

// Profile Top-Nav Dropdown toggler
function toggleProfileDropdown() {
  const dropdown = document.getElementById('profile-dropdown');
  if (dropdown) {
    dropdown.classList.toggle('hidden');
  }
}

// Modal open/save actions
function openProfileDetailsModal() {
  const modal = document.getElementById('profile-details-modal');
  if (!modal) return;
  
  document.getElementById('profile-display-name-input').value = currentUser;
  document.getElementById('profile-email-input').value = localStorage.getItem('finswarm_email') || '';
  document.getElementById('profile-role-input').value = localStorage.getItem('finswarm_role') || 'Market Observer';
  
  const hasKey = !!localStorage.getItem('finswarm_gemini_api_key');
  const statusIcon = document.getElementById('profile-key-status-icon');
  const statusText = document.getElementById('profile-key-status-text');
  
  if (hasKey) {
    statusIcon.style.color = '#10b981'; // Green
    statusText.textContent = 'Custom API Key Saved Locally';
  } else {
    statusIcon.style.color = '#f59e0b'; // Amber
    statusText.textContent = 'Using server-configured key (default)';
  }
  
  modal.classList.add('active');
  
  // Hide dropdown
  const dropdown = document.getElementById('profile-dropdown');
  if (dropdown) dropdown.classList.add('hidden');
}

async function saveProfileDetails() {
  const nameInput = document.getElementById('profile-display-name-input');
  const roleInput = document.getElementById('profile-role-input');
  const name = nameInput.value.trim();
  const role = roleInput.value;
  
  if (!name) {
    alert("Display name cannot be empty.");
    return;
  }
  
  const saveBtn = document.getElementById('save-profile-btn');
  const originalHtml = saveBtn.innerHTML;
  saveBtn.disabled = true;
  saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';
  
  try {
    // 1. Call backend profile update endpoint
    await apiUpdateProfile(name);
    
    // 2. Update localStorage
    localStorage.setItem('finswarm_user', name);
    localStorage.setItem('finswarm_role', role);
    currentUser = name;
    
    // 3. Update UI
    document.getElementById('user-profile-name').textContent = name;
    document.getElementById('user-profile-role').textContent = role;
    
    const initials = name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
    document.getElementById('user-avatar-initials').textContent = initials;
    document.getElementById('user-avatar-top').textContent = initials;
    
    document.getElementById('dropdown-user-name').textContent = name;
    document.getElementById('dropdown-user-role').textContent = role;
    
    document.getElementById('greeting-title').textContent = `What's new, ${name}?`;
    
    alert("Profile details updated successfully.");
    closeModal('profile-details-modal');
  } catch (err) {
    console.error("Failed to update profile details:", err);
    alert(`Failed to update profile details: ${err.message}`);
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerHTML = originalHtml;
  }
}
