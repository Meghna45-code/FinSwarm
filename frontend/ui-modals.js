// ==================== FRONTEND MODAL & OVERLAY CONTROLLERS ====================

let editingAgentKey = null;

function openExternalLink(url, event) {
  if (event) {
    if (typeof event.stopPropagation === 'function') event.stopPropagation();
    if (typeof event.preventDefault === 'function') event.preventDefault();
  }
  if (!url) return;
  const win = window.open(url, '_blank');
  if (win) win.focus();
}
window.openExternalLink = openExternalLink;

function switchSidebarTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
  
  if (tabName === 'company') {
    document.getElementById('tab-company-btn').classList.add('active');
    document.getElementById('tab-company').classList.add('active');
  } else if (tabName === 'agents') {
    document.getElementById('tab-agents-btn').classList.add('active');
    document.getElementById('tab-agents').classList.add('active');
  } else if (tabName === 'history') {
    document.getElementById('tab-history-btn').classList.add('active');
    document.getElementById('tab-history').classList.add('active');
    if (typeof loadHistory === 'function') {
      loadHistory();
    }
  }
}

function showAgentsConfigScreen() {
  if (playbackTimeoutId) {
    isPlaybackPaused = true;
    const pauseBtn = document.getElementById('btn-pause-debate');
    if (pauseBtn) pauseBtn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  
  if (simulationResult && simulationResult.state_tracking && currentPlaybackIndex > 0) {
    const trackingObj = simulationResult.state_tracking[currentPlaybackIndex];
    if (trackingObj && trackingObj.states) {
      const activeStates = trackingObj.states;
      Object.entries(activeStates).forEach(([name, state]) => {
        if (activeAgents[name]) {
          activeAgents[name].initial_sentiment = state.sentiment;
          activeAgents[name].initial_conviction = state.conviction;
          activeAgents[name].reactivity_threshold = state.reactivity_threshold;
        }
      });
    }
  }

  document.getElementById('agents-config-screen').classList.add('active');
  renderConfigAgentsGrid();
}

function closeModal(modalId) {
  document.getElementById(modalId).classList.remove('active');
}

function openModal(modalId) {
  document.getElementById(modalId).classList.add('active');
}

function openVerificationModal(turnNumber) {
  if (!simulationResult || !simulationResult.transcript) return;
  const turn = simulationResult.transcript.find(t => String(t.turn) === String(turnNumber));
  if (!turn) return;
  
  const titleEl = document.getElementById('verification-title');
  const bodyEl = document.getElementById('verification-body');
  if (!titleEl || !bodyEl) return;
  
  const accuracyPercent = turn.factuality_score !== undefined && turn.factuality_score !== null 
    ? Math.round(turn.factuality_score * 100) + '%' 
    : 'N/A';
  const isValid = turn.is_factually_correct;
  const statusBadge = isValid 
    ? `<span style="background: rgba(110, 231, 183, 0.2); color: #065f46; border: 1px solid rgba(110, 231, 183, 0.4); padding: 3px 8px; border-radius: 99px; font-weight: 600; font-size: 0.75rem; text-transform: uppercase;">Verified</span>`
    : `<span style="background: rgba(243, 162, 190, 0.22); color: #be185d; border: 1px solid rgba(243, 162, 190, 0.45); padding: 3px 8px; border-radius: 99px; font-weight: 600; font-size: 0.75rem; text-transform: uppercase;">Fact Check Warning</span>`;
    
  titleEl.textContent = `Turn #${turn.turn} Verification`;
  bodyEl.innerHTML = `
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border-color); padding-bottom: 8px;">
      <strong>Agent:</strong> <span>${escapeHTML(turn.speaker)}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
      <strong>Status:</strong> ${statusBadge}
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 4px;">
      <strong>Accuracy Score:</strong> <span>${accuracyPercent}</span>
    </div>
    <div style="margin-top: 8px;">
      <strong>Cited Source:</strong>
      <div style="background: rgba(129, 191, 183, 0.08); border: 1px solid rgba(129, 191, 183, 0.18); padding: 8px 12px; border-radius: var(--radius-sm); font-family: monospace; font-size: 0.8rem; margin-top: 4px; color: var(--text-main);">
        ${escapeHTML(turn.cited_source || 'Reliance AGM & SEC/SEBI Filing 2026')}
      </div>
    </div>
    <div style="margin-top: 10px; padding: 10px 12px; background: rgba(129, 191, 183, 0.12); border: 1px dashed var(--color-lavender); border-radius: var(--radius-sm);">
      <strong style="color: var(--color-lavender); font-size: 0.82rem;"><i class="fa-solid fa-link"></i> Direct Source Link:</strong><br/>
      <a href="${turn.source_url || 'https://www.ril.com/investors/financial-reporting'}" target="_blank" rel="noopener noreferrer" style="color: var(--color-lavender); font-weight: 600; text-decoration: underline; word-break: break-all; font-size: 0.85rem; display: inline-block; margin-top: 4px; cursor: pointer;">
        ${escapeHTML(turn.source_url || 'https://www.ril.com/investors/financial-reporting')} <i class="fa-solid fa-arrow-up-right-from-square"></i>
      </a>
    </div>
    <div style="margin-top: 8px;">
      <strong>Verification Run-down:</strong>
      <div style="margin-top: 4px; padding: 10px; border-radius: var(--radius-sm); background: ${isValid ? 'rgba(110, 231, 183, 0.08)' : 'rgba(243, 162, 190, 0.08)'}; border: 1px solid ${isValid ? 'rgba(110, 231, 183, 0.2)' : 'rgba(243, 162, 190, 0.2)'}; color: var(--text-main); font-size: 0.85rem;">
        ${escapeHTML(turn.moderator_note || (isValid ? 'The statement aligns with the ground truth company profile.' : 'Factual discrepancy detected.'))}
      </div>
    </div>
  `;
  
  openModal('verification-detail-modal');
}

window.openVerificationModal = openVerificationModal;

function handleAgentModalBackdropClick(event) {
  if (event.target === document.getElementById('agent-detail-modal')) {
    closeModal('agent-detail-modal');
  }
}

/**
 * Opens the Agent Detail modal.
 * @param {Object} agent - The agent data object passed directly from the card renderer.
 */
function openAgentDetailModal(agent) {
  if (!agent || typeof agent !== 'object') return;

  // ---- Avatar initials ----
  const initials = (agent.name || '').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase() || '??';
  document.getElementById('agent-detail-avatar').textContent = initials;

  // ---- Name & swarm badge ----
  document.getElementById('agent-detail-name').textContent = agent.name || 'Unknown Agent';

  const swarmBadge = document.getElementById('agent-detail-swarm-badge');
  let swarmClass = 'swarm-structural';
  let swarmLabel = 'Structural';
  const st = agent.swarm_type || '';
  if (st.includes('Retail'))  { swarmClass = 'swarm-retail';      swarmLabel = 'Retail';     }
  if (st.includes('Trading')) { swarmClass = 'swarm-analytical';  swarmLabel = 'Analytical'; }
  swarmBadge.className = `agent-swarm-tag ${swarmClass}`;
  swarmBadge.textContent = swarmLabel;

  // ---- Role ----
  document.getElementById('agent-detail-role').textContent = agent.role_identity || '';

  // ---- Stance badge ----
  const sentiment = parseFloat(agent.initial_sentiment || 0);
  const stanceBadge = document.getElementById('agent-detail-stance');
  if (sentiment > 0.15) {
    stanceBadge.textContent = '▲ Bullish';
    stanceBadge.className = 'agent-detail-stance-badge stance-bullish';
  } else if (sentiment < -0.15) {
    stanceBadge.textContent = '▼ Bearish';
    stanceBadge.className = 'agent-detail-stance-badge stance-bearish';
  } else {
    stanceBadge.textContent = '— Neutral';
    stanceBadge.className = 'agent-detail-stance-badge stance-neutral';
  }

  // ---- Sentiment bar (animate in) ----
  const sentimentPct = ((sentiment + 1) / 2) * 100;
  const sentValEl = document.getElementById('agent-detail-sentiment-val');
  const sentBarEl = document.getElementById('agent-detail-sentiment-bar');
  sentValEl.textContent = sentiment.toFixed(2);
  sentValEl.style.color = sentiment > 0.15 ? 'var(--color-green)' : sentiment < -0.15 ? 'var(--color-red)' : 'var(--text-muted)';
  sentBarEl.style.width = '0%';
  setTimeout(() => { sentBarEl.style.width = sentimentPct + '%'; }, 60);

  // ---- Conviction bar ----
  const conviction = parseFloat(agent.initial_conviction || 0.5);
  const convPct = conviction * 100;
  document.getElementById('agent-detail-conviction-val').textContent = Math.round(convPct) + '%';
  const convBarEl = document.getElementById('agent-detail-conviction-bar');
  convBarEl.style.width = '0%';
  setTimeout(() => { convBarEl.style.width = convPct + '%'; }, 100);

  // ---- Reactivity bar ----
  const reactivity = parseFloat(agent.reactivity_threshold || 0.3);
  const reactPct = reactivity * 100;
  document.getElementById('agent-detail-reactivity-val').textContent = Math.round(reactPct) + '%';
  const reactBarEl = document.getElementById('agent-detail-reactivity-bar');
  reactBarEl.style.width = '0%';
  setTimeout(() => { reactBarEl.style.width = reactPct + '%'; }, 140);

  // ---- Primary Metrics ----
  const metricsList = document.getElementById('agent-detail-metrics');
  metricsList.innerHTML = '';
  (agent.primary_metrics || []).forEach(m => {
    metricsList.innerHTML += `<li>${escapeHTML(String(m))}</li>`;
  });

  // ---- Cognitive Biases ----
  const biasesList = document.getElementById('agent-detail-biases');
  biasesList.innerHTML = '';
  (agent.cognitive_biases || []).forEach(b => {
    biasesList.innerHTML += `<li>${escapeHTML(String(b))}</li>`;
  });

  // ---- Linguistic Style ----
  document.getElementById('agent-detail-linguistic').textContent = agent.linguistic_style || '—';

  // ---- Reactions ----
  document.getElementById('agent-detail-good-reaction').textContent = agent.good_news_reaction || '—';
  document.getElementById('agent-detail-bad-reaction').textContent  = agent.bad_news_reaction  || '—';

  // ---- Avatar gradient color based on swarm type ----
  const avatarEl = document.getElementById('agent-detail-avatar');
  if (st.includes('Retail')) {
    avatarEl.style.background = 'linear-gradient(135deg, #d946ef, #a21caf)';
    avatarEl.style.boxShadow = '0 0 24px rgba(217, 70, 239, 0.4)';
  } else if (st.includes('Trading')) {
    avatarEl.style.background = 'linear-gradient(135deg, #f59e0b, #b45309)';
    avatarEl.style.boxShadow = '0 0 24px rgba(245, 158, 11, 0.4)';
  } else {
    avatarEl.style.background = 'linear-gradient(135deg, var(--color-secondary), var(--color-primary))';
    avatarEl.style.boxShadow = '0 0 24px rgba(6, 182, 212, 0.35)';
  }

  // ---- Open modal ----
  document.getElementById('agent-detail-modal').classList.add('active');
}

let selectedAgentKeys = null;

function renderConfigAgentsGrid() {
  const container = document.getElementById('agents-selection-grid');
  if (!container) return;
  
  const personaDescriptions = {
    "Brand Loyalist / Fanboy": "Enthusiastic retail investor driven by identity and community alignment. Sees company as revolutionary.",
    "Brand Skeptic": "Cynical consumer critic who dislikes corporate hype, pricing pressure, and customer service failures.",
    "Institutional Value Investor": "Rational long-term fund manager focused on intrinsic DCF valuation, ROIC, and Free Cash Flow.",
    "Aggressive Short-Seller": "Confrontational hedge fund manager hunting for debt covenant breaches, fraud, or execution bottlenecks.",
    "Technical Day Trader": "Fast-paced momentum trader who ignores fundamentals and trades purely on RSI, MACD, and breakout levels.",
    "Industry Tech Expert": "Veteran R&D engineer evaluating underlying product architecture, technical specs, and patent filings.",
    "Macro Economist": "Systemic theorist focused on Federal Reserve rates, CPI inflation, tariff policies, and global trade dynamics.",
    "Company Insider / Employee": "Operational voice concerned with internal shipping velocity, engineering friction, and executive stability.",
    "ESG Specialist": "Governance-focused ethical investor monitoring carbon footprint, labor disputes, and regulatory compliance.",
    "Panic-Prone Retail Trader": "Emotional trader driven by FOMO, social media hype, loss aversion, and rapid panic selling.",
    "Dividend Growth Investor": "Conservative income investor seeking dividend yield safety, payout ratio sustainability, and cash reserves.",
    "Algorithmic Quantitative Trader": "Formulaic statistical arbitrage bot executing trades based on historical volatility and correlations.",
    "Regulatory Compliance Watchdog": "Legalistic watchdog representing SEC/NHTSA compliance, antitrust probes, and regulatory fines.",
    "B2B Supply Chain Partner / Vanguard": "Pragmatic vendor monitoring supplier payment terms, order backlogs, and raw material bottlenecks."
  };

  const keysToRender = Object.keys(personaDescriptions);
  if (!selectedAgentKeys || selectedAgentKeys.size === 0) {
    selectedAgentKeys = new Set(keysToRender);
  }
  
  container.innerHTML = '';
  keysToRender.forEach(key => {
    const agent = (activeAgents && activeAgents[key]) || (defaultAgentsData && defaultAgentsData[key]) || { name: key, swarm_type: "Market Persona" };
    const isChecked = selectedAgentKeys.has(key);
    const desc = personaDescriptions[key];
    
    let swarmBadgeClass = "swarm-structural";
    let swarmLabel = "Structural";
    const st = agent.swarm_type || "";
    if (st.includes("Retail")) { swarmBadgeClass = "swarm-retail"; swarmLabel = "Retail"; }
    if (st.includes("Trading")) { swarmBadgeClass = "swarm-analytical"; swarmLabel = "Analytical"; }

    const cardHtml = `
      <div class="agent-select-card" style="background: #ffffff; border: 2px solid ${isChecked ? '#10b981' : '#cbd5e1'}; border-radius: var(--radius-md); padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; cursor: pointer; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.04);" onclick="toggleAgentCardSelection('${escapeHTML(key)}')">
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <input type="checkbox" id="chk-agent-${escapeHTML(key)}" ${isChecked ? 'checked' : ''} style="width: 18px; height: 18px; cursor: pointer; accent-color: #10b981;" onclick="event.stopPropagation(); toggleAgentCardSelection('${escapeHTML(key)}')">
            <span style="font-weight: 800; color: #0f172a; font-size: 0.98rem; text-shadow: none;">${escapeHTML(key)}</span>
          </div>
          <span class="agent-swarm-tag ${swarmBadgeClass}">${swarmLabel}</span>
        </div>
        <p style="font-size: 0.84rem; color: #475569; line-height: 1.45; margin: 0; font-weight: 500;">${escapeHTML(desc)}</p>
      </div>
    `;
    container.innerHTML += cardHtml;
  });
}

function toggleAgentCardSelection(key) {
  if (selectedAgentKeys.has(key)) {
    if (selectedAgentKeys.size <= 1) {
      alert("At least 1 agent must remain active for the debate.");
      return;
    }
    selectedAgentKeys.delete(key);
  } else {
    selectedAgentKeys.add(key);
  }
  renderConfigAgentsGrid();
}

function resetAgentsSelection() {
  selectedAgentKeys = new Set(Object.keys(activeAgents));
  renderConfigAgentsGrid();
}

function saveAgentsSelection() {
  // Filter activeAgents to only include checked keys
  const newActiveAgents = {};
  selectedAgentKeys.forEach(k => {
    if (activeAgents[k]) {
      newActiveAgents[k] = activeAgents[k];
    } else if (defaultAgentsData[k]) {
      newActiveAgents[k] = defaultAgentsData[k];
    }
  });
  activeAgents = newActiveAgents;
  renderAgentsList(activeAgents);
  closeModal('agents-config-screen');
}

function editAgentInForm(key) {
  const agent = activeAgents[key];
  if (!agent) return;
  
  editingAgentKey = key;
  document.getElementById('editor-title').textContent = `Edit Agent: ${agent.name}`;
  
  document.getElementById('editor-name').value = agent.name;
  document.getElementById('editor-swarm-type').value = agent.swarm_type;
  document.getElementById('editor-role').value = agent.role_identity;
  
  document.getElementById('editor-sentiment').value = agent.initial_sentiment;
  document.getElementById('editor-sentiment-val').textContent = parseFloat(agent.initial_sentiment).toFixed(1);
  
  document.getElementById('editor-conviction').value = agent.initial_conviction;
  document.getElementById('editor-conviction-val').textContent = Math.round(agent.initial_conviction * 100) + '%';
  
  document.getElementById('editor-reactivity').value = agent.reactivity_threshold;
  document.getElementById('editor-reactivity-val').textContent = Math.round(agent.reactivity_threshold * 100) + '%';

  sentimentManuallySet = true;
  convictionManuallySet = true;
  reactivityManuallySet = true;
}

function clearEditorForm() {
  editingAgentKey = null;
  document.getElementById('editor-title').textContent = "Add/Edit Swarm Agent";
  document.getElementById('editor-name').value = '';
  document.getElementById('editor-role').value = '';
  document.getElementById('editor-sentiment').value = 0.0;
  document.getElementById('editor-sentiment-val').textContent = '0.0';
  document.getElementById('editor-conviction').value = 0.5;
  document.getElementById('editor-conviction-val').textContent = '50%';
  document.getElementById('editor-reactivity').value = 0.3;
  document.getElementById('editor-reactivity-val').textContent = '30%';

  sentimentManuallySet = false;
  convictionManuallySet = false;
  reactivityManuallySet = false;
}

function deleteAgentFromConfig(key) {
  delete activeAgents[key];
  renderConfigAgentsTable();
  if (editingAgentKey === key) {
    clearEditorForm();
  }
}

function saveAgentFromForm() {
  const name = document.getElementById('editor-name').value.trim();
  if (!name) {
    alert("Please enter a name for the agent.");
    return;
  }
  
  const swarmType = document.getElementById('editor-swarm-type').value;
  const role = document.getElementById('editor-role').value.trim();
  const sentiment = parseFloat(document.getElementById('editor-sentiment').value);
  const conviction = parseFloat(document.getElementById('editor-conviction').value);
  const reactivity = parseFloat(document.getElementById('editor-reactivity').value);
  
  const agentKey = editingAgentKey || name;
  activeAgents[agentKey] = {
    name: name,
    swarm_type: swarmType,
    role_identity: role || `A financial observer focusing on ${name} strategies.`,
    primary_metrics: activeAgents[agentKey]?.primary_metrics || ["Stock price", "Sentiment dynamics"],
    cognitive_biases: activeAgents[agentKey]?.cognitive_biases || ["Anchoring Bias"],
    linguistic_style: activeAgents[agentKey]?.linguistic_style || "Pragmatic and professional.",
    good_news_reaction: activeAgents[agentKey]?.good_news_reaction || "Optimistic.",
    bad_news_reaction: activeAgents[agentKey]?.bad_news_reaction || "Pessimistic.",
    initial_sentiment: sentiment,
    initial_conviction: conviction,
    reactivity_threshold: reactivity,
    market_influence_weight: activeAgents[agentKey]?.market_influence_weight !== undefined ? activeAgents[agentKey].market_influence_weight : 0.2,
    social_influence_susceptibility: activeAgents[agentKey]?.social_influence_susceptibility !== undefined ? activeAgents[agentKey].social_influence_susceptibility : 0.5,
    risk_tolerance: activeAgents[agentKey]?.risk_tolerance !== undefined ? activeAgents[agentKey].risk_tolerance : 0.5,
    expertise_domains: activeAgents[agentKey]?.expertise_domains || []
  };
  
  renderConfigAgentsTable();
  clearEditorForm();
}

async function autofillAgentFromForm() {
  const name = document.getElementById('editor-name').value.trim();
  if (!name) {
    alert("Please enter at least a name for the agent so the AI knows who to generate!");
    return;
  }
  
  const autofillBtn = document.getElementById('editor-autofill-btn');
  autofillBtn.disabled = true;
  autofillBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Generating...';
  
  const partialAgent = {
    name: name,
    swarm_type: document.getElementById('editor-swarm-type').value,
    role_identity: document.getElementById('editor-role').value.trim() || undefined,
    initial_sentiment: sentimentManuallySet ? parseFloat(document.getElementById('editor-sentiment').value) : undefined,
    initial_conviction: convictionManuallySet ? parseFloat(document.getElementById('editor-conviction').value) : undefined,
    reactivity_threshold: reactivityManuallySet ? parseFloat(document.getElementById('editor-reactivity').value) : undefined
  };
  
  try {
    const completedAgent = await apiAutofillAgent(partialAgent, activeEnvironments, companyData);
    
    document.getElementById('editor-swarm-type').value = completedAgent.swarm_type || 'Retail & Consumer Swarm';
    document.getElementById('editor-role').value = completedAgent.role_identity || '';
    
    const sentiment = (completedAgent.initial_sentiment !== undefined && completedAgent.initial_sentiment !== null) ? parseFloat(completedAgent.initial_sentiment) : 0.0;
    document.getElementById('editor-sentiment').value = sentiment;
    document.getElementById('editor-sentiment-val').textContent = isNaN(sentiment) ? '0.0' : sentiment.toFixed(1);
    
    const conviction = (completedAgent.initial_conviction !== undefined && completedAgent.initial_conviction !== null) ? parseFloat(completedAgent.initial_conviction) : 0.5;
    document.getElementById('editor-conviction').value = conviction;
    document.getElementById('editor-conviction-val').textContent = isNaN(conviction) ? '50%' : Math.round(conviction * 100) + '%';
    
    const reactivity = (completedAgent.reactivity_threshold !== undefined && completedAgent.reactivity_threshold !== null) ? parseFloat(completedAgent.reactivity_threshold) : 0.3;
    document.getElementById('editor-reactivity').value = reactivity;
    document.getElementById('editor-reactivity-val').textContent = isNaN(reactivity) ? '30%' : Math.round(reactivity * 100) + '%';
    
    sentimentManuallySet = true;
    convictionManuallySet = true;
    reactivityManuallySet = true;

    const agentKey = editingAgentKey || name;
    activeAgents[agentKey] = {
      ...activeAgents[agentKey],
      ...completedAgent,
      initial_sentiment: sentiment,
      initial_conviction: conviction,
      reactivity_threshold: reactivity
    };
  } catch (error) {
    console.error("AI Autofill Error:", error);
    alert("AI Autofill failed. Offline fallback applied.");
  } finally {
    autofillBtn.disabled = false;
    autofillBtn.innerHTML = '<i class="fa-solid fa-wand-magic-sparkles"></i> Autofill / Fix with AI';
  }
}

function resetConfigAgents() {
  activeAgents = JSON.parse(JSON.stringify(defaultAgentsData));
  renderConfigAgentsTable();
  clearEditorForm();
}

function launchMainWorkspace() {
  if (Object.keys(activeAgents).length === 0) {
    alert("You must have at least one active agent in the swarm to run the simulation!");
    return;
  }
  
  renderAgentsList(activeAgents);
  closeModal('agents-config-screen');
  
  if (simulationResult && currentPlaybackIndex > 0 && currentPlaybackIndex < simulationResult.transcript.length) {
    resumeSimulation();
  }
}

function showEnvConfigScreen() {
  if (playbackTimeoutId) {
    isPlaybackPaused = true;
    const pauseBtn = document.getElementById('btn-pause-debate');
    if (pauseBtn) pauseBtn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  
  document.getElementById('env-ceo').value = activeEnvironments["CEO Status"] || 'Normal';
  
  const rates = activeEnvironments["Interest Rates"] !== undefined && activeEnvironments["Interest Rates"] !== 'Steady' && activeEnvironments["Interest Rates"] !== '' ? parseFloat(activeEnvironments["Interest Rates"]) : 0.0;
  document.getElementById('env-rates').value = rates;
  document.getElementById('env-rates-val').textContent = (rates >= 0 ? '+' : '') + rates.toFixed(2) + '%';
  
  const supply = activeEnvironments["Supply Chain"] !== undefined && activeEnvironments["Supply Chain"] !== 'Healthy' && activeEnvironments["Supply Chain"] !== '' ? parseInt(activeEnvironments["Supply Chain"]) : 0;
  document.getElementById('env-supply').value = supply;
  document.getElementById('env-supply-val').textContent = supply + '%';
  
  const regulatory = activeEnvironments["Regulatory Pressure"] !== undefined && activeEnvironments["Regulatory Pressure"] !== 'Compliant' && activeEnvironments["Regulatory Pressure"] !== '' ? parseInt(activeEnvironments["Regulatory Pressure"]) : 0;
  document.getElementById('env-regulatory').value = regulatory;
  document.getElementById('env-regulatory-val').textContent = regulatory + '%';
  
  const competitor = activeEnvironments["Competitor Threat"] !== undefined && activeEnvironments["Competitor Threat"] !== 'Steady' && activeEnvironments["Competitor Threat"] !== '' ? parseInt(activeEnvironments["Competitor Threat"]) : 0;
  document.getElementById('env-competitor').value = competitor;
  document.getElementById('env-competitor-val').textContent = competitor + '%';
  
  const market = activeEnvironments["Market Sentiment"] !== undefined && activeEnvironments["Market Sentiment"] !== 'Neutral' && activeEnvironments["Market Sentiment"] !== '' ? parseInt(activeEnvironments["Market Sentiment"]) : 0;
  document.getElementById('env-market').value = market;
  document.getElementById('env-market-val').textContent = market + '%';
  
  const labor = activeEnvironments["Labor Relations"] !== undefined && activeEnvironments["Labor Relations"] !== 'Stable' && activeEnvironments["Labor Relations"] !== '' ? parseInt(activeEnvironments["Labor Relations"]) : 0;
  document.getElementById('env-labor').value = labor;
  document.getElementById('env-labor-val').textContent = labor + '%';

  document.getElementById('env-custom').value = activeEnvironments["Custom Scenario"] || '';

  document.getElementById('env-rates').oninput = function() {
    const val = parseFloat(this.value);
    document.getElementById('env-rates-val').textContent = (val >= 0 ? '+' : '') + val.toFixed(2) + '%';
  };
  ['supply', 'regulatory', 'competitor', 'market', 'labor'].forEach(id => {
    document.getElementById(`env-${id}`).oninput = function() {
      document.getElementById(`env-${id}-val`).textContent = this.value + '%';
    };
  });

  document.getElementById('env-config-screen').classList.add('active');
  
  if (companyData && companyData.name) {
    document.getElementById('env-company-name').textContent = companyData.name;
    document.getElementById('env-company-ticker').textContent = companyData.ticker;
    document.getElementById('env-company-desc').textContent = companyData.description;
    
    const envMetricsGrid = document.getElementById('env-company-metrics');
    envMetricsGrid.innerHTML = '';
    if (companyData.key_metrics) {
      for (const [key, value] of Object.entries(companyData.key_metrics)) {
        envMetricsGrid.innerHTML += `
          <div style="background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: var(--radius-sm); display: flex; flex-direction: column; gap: 4px;">
            <span style="font-size: 0.75rem; color: var(--text-muted);">${escapeHTML(key)}</span>
            <span style="font-size: 0.95rem; font-weight: 700; color: white;">${escapeHTML(value)}</span>
          </div>
        `;
      }
    }
  }
  
  document.getElementById('env-reset-btn').onclick = resetEnvConfigFields;
  document.getElementById('env-launch-btn').onclick = launchSimulationWorkspace;
}

function resetEnvConfigFields() {
  document.getElementById('env-ceo').value = 'Normal';
  
  document.getElementById('env-rates').value = 0.0;
  document.getElementById('env-rates-val').textContent = '0.00%';
  
  ['supply', 'regulatory', 'competitor', 'market', 'labor'].forEach(id => {
    document.getElementById(`env-${id}`).value = 0;
    document.getElementById(`env-${id}-val`).textContent = '0%';
  });
  
  document.getElementById('env-custom').value = '';
}

async function launchSimulationWorkspace() {
  const envLaunchBtn = document.getElementById('env-launch-btn');
  envLaunchBtn.disabled = true;
  const originalText = envLaunchBtn.innerHTML;
  envLaunchBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Contextualizing Swarm...';

  activeEnvironments = {
    "CEO Status": document.getElementById('env-ceo').value,
    "Interest Rates": document.getElementById('env-rates').value,
    "Supply Chain": document.getElementById('env-supply').value,
    "Regulatory Pressure": document.getElementById('env-regulatory').value,
    "Competitor Threat": document.getElementById('env-competitor').value,
    "Market Sentiment": document.getElementById('env-market').value,
    "Labor Relations": document.getElementById('env-labor').value,
    "Custom Scenario": document.getElementById('env-custom').value.trim()
  };
  
  try {
    const adjustedPersonas = await apiContextualizePersonas(activeEnvironments, companyData);
    activeAgents = adjustedPersonas;
    
    closeModal('env-config-screen');
    renderAgentsList(activeAgents);
    
    if (simulationResult && currentPlaybackIndex > 0 && currentPlaybackIndex < simulationResult.transcript.length) {
      resumeSimulation();
    }
  } catch (error) {
    console.error("Error during LLM contextualization, falling back to default/baseline adjustment:", error);
    closeModal('env-config-screen');
    renderAgentsList(activeAgents);
    if (simulationResult && currentPlaybackIndex > 0 && currentPlaybackIndex < simulationResult.transcript.length) {
      resumeSimulation();
    }
  } finally {
    envLaunchBtn.disabled = false;
    envLaunchBtn.innerHTML = originalText;
  }
}

async function handleSwarmCommand() {
  const inputEl = document.getElementById('swarm-command-input');
  const commandText = inputEl.value.trim();
  if (!commandText) {
    alert("Please enter a swarm adjustment command.");
    return;
  }

  const swarmCmdBtn = document.getElementById('swarm-command-btn');
  swarmCmdBtn.disabled = true;
  const originalText = swarmCmdBtn.innerHTML;
  swarmCmdBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Executing...';

  try {
    const updatedAgents = await apiSendSwarmCommand(commandText, activeAgents, activeEnvironments, companyData);
    activeAgents = updatedAgents;
    renderConfigAgentsTable();
    renderAgentsList(activeAgents);
    inputEl.value = '';
  } catch (error) {
    console.error("Swarm Command Error:", error);
    alert("Error executing command. Make sure the backend server is running.");
  } finally {
    swarmCmdBtn.disabled = false;
    swarmCmdBtn.innerHTML = originalText;
  }
}

// Obfuscation helpers to avoid storing plaintext strings in local storage
function obfuscateKey(key) {
  if (!key) return '';
  return btoa(key.split('').reverse().join(''));
}

function deobfuscateKey(obfuscated) {
  if (!obfuscated) return '';
  try {
    return atob(obfuscated).split('').reverse().join('');
  } catch (e) {
    return '';
  }
}

function toggleApiKeyInput() {
  const modal = document.getElementById('api-key-screen');
  const input = document.getElementById('gemini-api-key-input');
  
  if (modal.classList.contains('active')) {
    modal.classList.remove('active');
  } else {
    const savedObfuscated = localStorage.getItem('finswarm_gemini_api_key') || '';
    input.value = deobfuscateKey(savedObfuscated);
    modal.classList.add('active');
  }
}

function saveApiKey() {
  const input = document.getElementById('gemini-api-key-input');
  const val = input.value.trim();
  if (val) {
    localStorage.setItem('finswarm_gemini_api_key', obfuscateKey(val));
    alert("Gemini API Key saved locally (obfuscated).");
  } else {
    localStorage.removeItem('finswarm_gemini_api_key');
    alert("Key cleared.");
  }
  closeModal('api-key-screen');
}

function clearApiKey() {
  localStorage.removeItem('finswarm_gemini_api_key');
  document.getElementById('gemini-api-key-input').value = '';
  alert("Gemini API Key cleared from local storage.");
  closeModal('api-key-screen');
}
