// ==================== FINSWARM API CLIENT ====================

const API_BASE = '';

function getApiKeyHeader() {
  const headers = {};
  
  const obfuscated = localStorage.getItem('finswarm_gemini_api_key');
  if (obfuscated) {
    try {
      const key = atob(obfuscated).split('').reverse().join('');
      if (key) headers['X-Gemini-API-Key'] = key;
    } catch (e) {
      console.warn("Failed to deobfuscate key:", e);
    }
  }

  const token = localStorage.getItem('finswarm_access_token');
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  
  return headers;
}

/**
 * Fetches default company profile.
 */
async function apiGetCompanyProfile(ticker = null) {
  const url = ticker ? `${API_BASE}/api/company?ticker=${encodeURIComponent(ticker)}` : `${API_BASE}/api/company`;
  const res = await fetch(url, {
    headers: {
      ...getApiKeyHeader()
    }
  });
  if (!res.ok) throw new Error("Failed to load company profile");
  return await res.json();
}

/**
 * Fetches baseline agent personas.
 */
async function apiGetPersonas() {
  const res = await fetch(`${API_BASE}/api/personas`, {
    headers: { ...getApiKeyHeader() }
  });
  if (!res.ok) throw new Error("Failed to load agent personas");
  return await res.json();
}

/**
 * Submits a new news simulation request.
 */
async function apiRunSimulation(newsContent, maxRounds, customAgents, environmentalVariables) {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({
      news_content: newsContent,
      max_rounds: maxRounds,
      custom_agents: customAgents,
      environmental_variables: environmentalVariables
    })
  });
  if (!res.ok) throw new Error("Simulation request failed");
  return res;
}

/**
 * Resumes an existing simulation from historical transcripts and state tracking.
 */
async function apiResumeSimulation(newsContent, maxRounds, customAgents, environmentalVariables, existingTranscript, existingStateHistory) {
  const res = await fetch(`${API_BASE}/api/simulate`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({
      news_content: newsContent,
      max_rounds: maxRounds,
      custom_agents: customAgents,
      environmental_variables: environmentalVariables,
      existing_transcript: existingTranscript,
      existing_state_history: existingStateHistory
    })
  });
  if (!res.ok) throw new Error("Resume simulation request failed");
  return res;
}

/**
 * Autofills blank fields of a custom agent persona.
 */
async function apiAutofillAgent(agent, environmentalVariables, companyProfile) {
  const res = await fetch(`${API_BASE}/api/agents/autofill`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({
      agent: agent,
      environmental_variables: environmentalVariables,
      company_profile: companyProfile
    })
  });
  if (!res.ok) throw new Error("AI Autofill failed");
  return await res.json();
}

/**
 * Adjusts initial parameters of agent personas based on environmental variables.
 */
async function apiContextualizePersonas(environmentalVariables, companyProfile) {
  const res = await fetch(`${API_BASE}/api/personas/contextualize`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({
      environmental_variables: environmentalVariables,
      company_profile: companyProfile
    })
  });
  if (!res.ok) throw new Error("Contextualization failed");
  return await res.json();
}

/**
 * Applies natural language command modifications to active agent personas list.
 */
async function apiSendSwarmCommand(command, currentAgents, environmentalVariables, companyProfile) {
  const res = await fetch(`${API_BASE}/api/agents/command`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({
      command: command,
      current_agents: currentAgents,
      environmental_variables: environmentalVariables,
      company_profile: companyProfile
    })
  });
  if (!res.ok) throw new Error("Swarm command execution failed");
  return await res.json();
}

/**
 * Uploads a PDF to the backend for layout-preserved text extraction.
 */
async function apiUploadPdf(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}/api/upload-pdf`, {
    method: 'POST',
    headers: { ...getApiKeyHeader() },
    body: formData
  });
  if (!res.ok) throw new Error("Failed to extract PDF text from server");
  const data = await res.json();
  return data.text;
}

/**
 * Retrieves all saved debates from history.
 */
async function apiGetDebates() {
  const res = await fetch(`${API_BASE}/api/debates`, {
    headers: { ...getApiKeyHeader() }
  });
  if (!res.ok) throw new Error("Failed to load historical debates list");
  return await res.json();
}

/**
 * Retrieves details for a specific saved debate.
 */
async function apiGetDebateDetails(debateId) {
  const res = await fetch(`${API_BASE}/api/debates/${debateId}`, {
    headers: {
      ...getApiKeyHeader()
    }
  });
  if (!res.ok) throw new Error("Failed to load debate details");
  return await res.json();
}

/**
 * Registers a new user.
 */
async function apiRegister(email, displayName, password) {
  const res = await fetch(`${API_BASE}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, display_name: displayName, password })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Registration failed");
  }
  return await res.json();
}

/**
 * Logins an existing user, returns access token.
 */
async function apiLogin(email, password) {
  const res = await fetch(`${API_BASE}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Login failed");
  }
  return await res.json();
}

/**
 * Initiates forgot password flow (generates OTP).
 */
async function apiForgotPassword(email) {
  const res = await fetch(`${API_BASE}/api/auth/forgot-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Reset request failed");
  }
  return await res.json();
}

/**
 * Resets password using OTP PIN.
 */
async function apiResetPassword(email, pin, newPassword) {
  const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, pin, new_password: newPassword })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Password reset failed");
  }
  return await res.json();
}

/**
 * Verifies OTP PIN.
 */
async function apiVerifyResetPin(email, pin) {
  const res = await fetch(`${API_BASE}/api/auth/verify-reset-pin`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, pin })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Invalid or expired reset PIN");
  }
  return await res.json();
}

/**
 * Updates the user's profile display name.
 */
async function apiUpdateProfile(displayName) {
  const res = await fetch(`${API_BASE}/api/auth/update-profile`, {
    method: 'POST',
    headers: { 
      'Content-Type': 'application/json',
      ...getApiKeyHeader()
    },
    body: JSON.stringify({ display_name: displayName })
  });
  if (!res.ok) {
    const errData = await res.json();
    throw new Error(errData.detail || "Failed to update profile details");
  }
  return await res.json();
}



