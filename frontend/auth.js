// ==================== AUTH — NO-LOGIN BYPASS MODE ====================
// Login pipeline has been removed. App launches directly into the workspace.

function initAuth() {
  // Bypass all authentication — jump straight to the workspace
  currentUser = 'FinSwarm User';
  loginSuccess(false);
}

function loginSuccess(showTutorialOnLogin = false) {
  // Safely update greeting if element exists
  const greetingEl = document.getElementById('greeting-title');
  if (greetingEl) greetingEl.textContent = `What's new, User?`;

  // Hide auth screen if it still exists
  const authScreen = document.getElementById('auth-screen');
  if (authScreen) authScreen.classList.remove('active');

  // Show main screen
  const mainScreen = document.getElementById('main-screen');
  if (mainScreen) mainScreen.classList.add('active');

  // Load sidebar agent personas
  loadSidebarData();

  // Never show tutorial — always go straight to workspace
}

function handleLogout() {
  // No-op — login removed
}

function showAuthForm(formName) {
  // No-op — login forms removed
}

function toggleProfileDropdown() {
  const dropdown = document.getElementById('profile-dropdown');
  if (dropdown) dropdown.classList.toggle('hidden');
}

function openProfileDetailsModal() {
  // No-op — profile modal removed
}

async function saveProfileDetails() {
  // No-op — profile modal removed
}

async function handleSignInSubmit() {
  // No-op — login removed
}

async function handleRegisterSubmit() {
  // No-op — login removed
}

async function handleForgotPasswordSubmit() {
  // No-op — login removed
}

async function handleVerifyResetPinSubmit() {
  // No-op — login removed
}

async function handleResetPasswordSubmit() {
  // No-op — login removed
}
