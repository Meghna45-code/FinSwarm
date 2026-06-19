// ==================== FRONTEND DOM RENDERERS & TEMPLATES ====================

// HTML Escaping Utility to prevent XSS vulnerabilities
function escapeHTML(str) {
  if (typeof str !== 'string') {
    if (str === null || str === undefined) return '';
    return String(str);
  }
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function getSentimentColor(val) {
  if (val > 0.15) return "var(--color-green)";
  if (val < -0.15) return "var(--color-red)";
  return "var(--text-muted)";
}

function getSwarmTypeClass(swarmType) {
  if (swarmType.includes("Retail")) return "swarm-retail";
  if (swarmType.includes("Trading")) return "swarm-analytical";
  return "swarm-structural";
}

function getSwarmAvatarClass(swarmType) {
  if (swarmType.includes("Retail")) return "avatar-retail";
  if (swarmType.includes("Trading")) return "avatar-analytical";
  return "avatar-structural";
}

function getSwarmPrimaryColor(swarmType) {
  if (swarmType.includes("Retail")) return "#d946ef";
  if (swarmType.includes("Trading")) return "#f59e0b";
  return "#10b981";
}

function renderCompanyProfile(company) {
  document.getElementById('company-loading').classList.add('hidden');
  document.getElementById('company-profile-view').classList.remove('hidden');
  const emptyState = document.getElementById('company-empty-state');
  if (emptyState) emptyState.style.display = 'none';
  
  document.getElementById('company-name').textContent = company.name;
  document.getElementById('company-ticker').textContent = company.ticker;
  document.getElementById('company-desc').textContent = company.description;
  document.getElementById('company-sector-industry').innerHTML = `${escapeHTML(company.sector)} &bull; ${escapeHTML(company.industry)}`;
  
  // Render key metrics
  const metricsGrid = document.getElementById('company-metrics');
  metricsGrid.innerHTML = '';
  for (const [key, value] of Object.entries(company.key_metrics)) {
    metricsGrid.innerHTML += `
      <div class="metric-card">
        <span class="metric-title">${escapeHTML(key)}</span>
        <span class="metric-val">${escapeHTML(value)}</span>
      </div>
    `;
  }
  
  // Render recent corporate events
  const eventsList = document.getElementById('company-events');
  eventsList.innerHTML = '';
  (company.recent_events || []).forEach(evt => {
    eventsList.innerHTML += `<li>${escapeHTML(evt)}</li>`;
  });
  
  // Render recent news (past 2-3 years) — prefer recent_news, fall back to historical_news
  const recentNewsList = document.getElementById('company-recent-news');
  if (recentNewsList) {
    recentNewsList.innerHTML = '';
    const items = (company.recent_news && company.recent_news.length > 0)
      ? company.recent_news
      : (company.historical_news || []);
    if (items.length === 0) {
      recentNewsList.innerHTML = `<p style="font-size:0.78rem;color:var(--text-dark);padding:6px 0;">No recent news available.</p>`;
    } else {
      items.forEach(news => {
        recentNewsList.innerHTML += `
          <div class="news-item">
            <span class="news-date">${escapeHTML(news.date)}</span>
            <h4 class="news-title">${escapeHTML(news.title)}</h4>
            <p class="news-summary">${escapeHTML(news.summary)}</p>
          </div>
        `;
      });
    }
  }

  // Populate History tab with company's full historical timeline
  renderCompanyHistoryTab(company);
}

function renderCompanyHistoryTab(company) {
  const section = document.getElementById('history-company-section');
  const header  = document.getElementById('history-company-header');
  const list    = document.getElementById('history-milestones-list');
  if (!section || !header || !list) return;

  // Header badge showing company name
  header.innerHTML = `
    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
      <span style="font-size:0.95rem;font-weight:700;color:white;">${escapeHTML(company.name)}</span>
      <span class="ticker-badge" style="font-size:0.68rem;padding:2px 7px;">${escapeHTML(company.ticker)}</span>
    </div>
    <p style="font-size:0.75rem;color:var(--text-muted);line-height:1.4;">${escapeHTML(company.description)}</p>
  `;

  list.innerHTML = '';
  const milestones = (company.historical_milestones && company.historical_milestones.length > 0)
    ? company.historical_milestones
    : (company.historical_news || []);

  if (milestones.length === 0) {
    list.innerHTML = `<p style="font-size:0.78rem;color:var(--text-dark);padding:6px 0;">No historical data available yet.</p>`;
  } else {
    milestones.forEach(item => {
      list.innerHTML += `
        <div class="news-item" style="border-left-color: var(--color-primary);">
          <span class="news-date">${escapeHTML(item.date)}</span>
          <h4 class="news-title">${escapeHTML(item.title)}</h4>
          <p class="news-summary">${escapeHTML(item.summary)}</p>
        </div>
      `;
    });
  }

  section.classList.remove('hidden');
}

function renderAgentsList(personas) {
  const listContainer = document.getElementById('agents-list');
  listContainer.innerHTML = '';
  
  Object.entries(personas).forEach(([key, value]) => {
    const typeClass = getSwarmTypeClass(value.swarm_type);
    const shortType = value.swarm_type.split(' ')[0];
    const initialSentiment = parseFloat(value.initial_sentiment || 0.0);
    const initialConviction = parseFloat(value.initial_conviction || 0.5);
    const sentimentPct = ((initialSentiment + 1) / 2) * 100;
    const convictionPct = initialConviction * 100;
    
    const card = document.createElement('div');
    card.className = 'agent-sidebar-card';
    card.setAttribute('data-agent-name', value.name.toLowerCase());
    card.setAttribute('data-agent-key', key);

    card.innerHTML = `
      <div class="agent-card-top">
        <h4>${escapeHTML(value.name)}</h4>
        <span class="agent-swarm-tag ${escapeHTML(typeClass)}">${escapeHTML(shortType)}</span>
      </div>
      <p class="agent-card-role">${escapeHTML(value.role_identity)}</p>
      
      <!-- Sidebar Dynamic Stats Indicators -->
      <div class="agent-card-stats-wrapper" style="margin-top: 10px; display: flex; flex-direction: column; gap: 6px; border-top: 1px solid rgba(255,255,255,0.03); padding-top: 8px;">
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem;">
          <span style="color: var(--text-muted);">Sentiment:</span>
          <strong class="sidebar-sentiment-val" style="color: ${getSentimentColor(initialSentiment)};">${initialSentiment.toFixed(2)}</strong>
        </div>
        <div style="height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden;">
          <div class="sidebar-sentiment-bar" style="width: ${sentimentPct}%; height: 100%; background: ${getSentimentColor(initialSentiment)}; transition: width 0.3s ease, background 0.3s ease;"></div>
        </div>
        
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem; margin-top: 2px;">
          <span style="color: var(--text-muted);">Conviction:</span>
          <strong class="sidebar-conviction-val" style="color: white;">${Math.round(convictionPct)}%</strong>
        </div>
        <div style="height: 4px; background: rgba(255,255,255,0.05); border-radius: 2px; overflow: hidden;">
          <div class="sidebar-conviction-bar" style="width: ${convictionPct}%; height: 100%; background: var(--color-blue); transition: width 0.3s ease;"></div>
        </div>
      </div>
    `;

    // Whale button — appended separately so onclick closure captures `value` directly
    const whaleBtn = document.createElement('button');
    whaleBtn.className = 'agent-whale-btn';
    whaleBtn.setAttribute('aria-label', 'View full agent profile');
    whaleBtn.innerHTML = '🐳';
    whaleBtn.onclick = (e) => {
      e.stopPropagation();
      openAgentDetailModal(value); // pass data object directly — no key lookup needed
    };
    card.appendChild(whaleBtn);

    listContainer.appendChild(card);
  });
}

/**
 * Renders a compact, always-visible roster of the 14 debate agents into a target container.
 * Used in the Company and History sidebar tabs so agents are always visible.
 */
function renderAgentRoster(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = '';

  if (!personasData || Object.keys(personasData).length === 0) {
    container.innerHTML = `<div style="font-size:0.75rem;color:var(--text-dark);text-align:center;padding:8px 0;">Agents loading...</div>`;
    return;
  }

  Object.entries(personasData).forEach(([key, agent]) => {
    const swarmType = agent.swarm_type || '';
    let stripeClass = 'stripe-structural';
    let badgeClass  = 'swarm-structural';
    let swarmLabel  = 'Structural';
    if (swarmType.includes('Retail')) {
      stripeClass = 'stripe-retail';
      badgeClass  = 'swarm-retail';
      swarmLabel  = 'Retail';
    } else if (swarmType.includes('Trading')) {
      stripeClass = 'stripe-analytical';
      badgeClass  = 'swarm-analytical';
      swarmLabel  = 'Analytical';
    }

    const sentiment = parseFloat(agent.initial_sentiment || 0);
    let dotClass = 'dot-neutral';
    let stance   = 'Neutral';
    if (sentiment > 0.15) { dotClass = 'dot-bullish'; stance = 'Bullish'; }
    else if (sentiment < -0.15) { dotClass = 'dot-bearish'; stance = 'Bearish'; }

    const pill = document.createElement('div');
    pill.className = 'agent-roster-pill';
    pill.title = agent.role_identity || agent.name;
    pill.innerHTML = `
      <div class="agent-roster-pill-stripe ${stripeClass}"></div>
      <div class="agent-roster-pill-info">
        <div class="agent-roster-pill-name">${escapeHTML(agent.name)}</div>
        <div class="agent-roster-pill-meta">
          <span class="agent-roster-swarm-badge ${badgeClass}">${escapeHTML(swarmLabel)}</span>
          <span style="font-size:0.6rem;color:var(--text-dark);">${escapeHTML(stance)}</span>
        </div>
      </div>
      <div class="agent-roster-sentiment-dot ${dotClass}"></div>
    `;
    container.appendChild(pill);
  });
}

function filterAgents() {
  const query = document.getElementById('agent-search-input').value.toLowerCase().trim();
  const cards = document.querySelectorAll('.agent-sidebar-card');
  
  cards.forEach(card => {
    const name = card.getAttribute('data-agent-name');
    if (name.includes(query)) {
      card.style.display = 'block';
    } else {
      card.style.display = 'none';
    }
  });
}

function initLiveMonitorColumn() {
  const grid = document.getElementById('live-agent-monitor-grid');
  if (!grid) return;
  grid.innerHTML = '';
  
  Object.entries(activeAgents).forEach(([name, persona]) => {
    const typeClass = getSwarmTypeClass(persona.swarm_type);
    const shortType = persona.swarm_type.split(' ')[0];
    const initialSentiment = parseFloat(persona.initial_sentiment || 0.0);
    const initialConviction = parseFloat(persona.initial_conviction || 0.5);
    const sentimentPct = ((initialSentiment + 1) / 2) * 100;
    const convictionPct = initialConviction * 100;
    
    grid.innerHTML += `
      <div class="live-monitor-card" data-monitor-agent-name="${escapeHTML(name)}">
        <div class="live-monitor-card-header">
          <h4>${escapeHTML(name)}</h4>
          <span class="${escapeHTML(typeClass)}">${escapeHTML(shortType)}</span>
        </div>
        
        <div class="live-monitor-slider-row" style="margin-top: 4px;">
          <span class="live-monitor-slider-label">Sentiment:</span>
          <span class="live-monitor-slider-val monitor-sentiment-val" style="color: ${getSentimentColor(initialSentiment)};">${initialSentiment.toFixed(2)}</span>
        </div>
        <div class="live-monitor-bar-track">
          <div class="live-monitor-bar-fill monitor-sentiment-bar" style="width: ${sentimentPct}%; background: ${getSentimentColor(initialSentiment)};"></div>
        </div>
        
        <div class="live-monitor-slider-row" style="margin-top: 4px;">
          <span class="live-monitor-slider-label">Conviction:</span>
          <span class="live-monitor-slider-val monitor-conviction-val" style="color: white;">${Math.round(convictionPct)}%</span>
        </div>
        <div class="live-monitor-bar-track">
          <div class="live-monitor-bar-fill monitor-conviction-bar" style="width: ${convictionPct}%; background: var(--color-blue);"></div>
        </div>
      </div>
    `;
  });
}

function updateLiveMonitorColumn(states, speakingAgentName) {
  Object.entries(states).forEach(([name, state]) => {
    const card = document.querySelector(`.live-monitor-card[data-monitor-agent-name="${name}"]`);
    if (card) {
      if (name.toLowerCase() === speakingAgentName.toLowerCase()) {
        card.classList.add('speaking');
      } else {
        card.classList.remove('speaking');
      }
      
      const sentValEl = card.querySelector('.monitor-sentiment-val');
      const sentBarEl = card.querySelector('.monitor-sentiment-bar');
      const convValEl = card.querySelector('.monitor-conviction-val');
      const convBarEl = card.querySelector('.monitor-conviction-bar');
      
      if (sentValEl && sentBarEl) {
        sentValEl.textContent = state.sentiment.toFixed(2);
        sentValEl.style.color = getSentimentColor(state.sentiment);
        
        const sentimentPct = ((state.sentiment + 1) / 2) * 100;
        sentBarEl.style.width = `${sentimentPct}%`;
        sentBarEl.style.background = getSentimentColor(state.sentiment);
      }
      
      if (convValEl && convBarEl) {
        convValEl.textContent = `${Math.round(state.conviction * 100)}%`;
        convBarEl.style.width = `${state.conviction * 100}%`;
      }
    }
  });
}

function updateSidebarAgentsParameters(states) {
  Object.entries(states).forEach(([name, state]) => {
    const cards = document.querySelectorAll('.agent-sidebar-card');
    let targetCard = null;
    cards.forEach(card => {
      if (card.querySelector('h4').textContent.trim().toLowerCase() === name.toLowerCase()) {
        targetCard = card;
      }
    });
    
    if (targetCard) {
      const sentValEl = targetCard.querySelector('.sidebar-sentiment-val');
      const sentBarEl = targetCard.querySelector('.sidebar-sentiment-bar');
      const convValEl = targetCard.querySelector('.sidebar-conviction-val');
      const convBarEl = targetCard.querySelector('.sidebar-conviction-bar');
      
      if (sentValEl && sentBarEl) {
        sentValEl.textContent = state.sentiment.toFixed(2);
        sentValEl.style.color = getSentimentColor(state.sentiment);
        
        const sentimentPct = ((state.sentiment + 1) / 2) * 100;
        sentBarEl.style.width = `${sentimentPct}%`;
        sentBarEl.style.background = getSentimentColor(state.sentiment);
      }
      
      if (convValEl && convBarEl) {
        convValEl.textContent = `${Math.round(state.conviction * 100)}%`;
        convBarEl.style.width = `${state.conviction * 100}%`;
      }
    }
  });
}

function appendTurnToTimeline(turn) {
  const container = document.getElementById('debate-timeline-messages');
  const isMod = turn.speaker === "Moderator" || !personasData[turn.speaker];
  
  let swarmType = "Moderator Guard";
  let swarmClass = "swarm-structural";
  let avatarClass = "avatar-moderator";
  let initialName = "MOD";
  
  if (!isMod && personasData[turn.speaker]) {
    const p = personasData[turn.speaker];
    swarmType = p.swarm_type;
    swarmClass = getSwarmTypeClass(p.swarm_type);
    avatarClass = getSwarmAvatarClass(p.swarm_type);
    initialName = p.name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase();
  }
  
  const turnCard = document.createElement('div');
  turnCard.className = 'debate-bubble';
  turnCard.setAttribute('data-turn-number', turn.turn);
  
  let slidersHtml = '';
  if (!isMod) {
    const sentimentVal = ((turn.sentiment_after + 1) / 2) * 100;
    const convictionVal = turn.conviction_after * 100;
    
    slidersHtml = `
      <div class="agent-live-sliders">
        <div class="live-slider-item">
          <div class="slider-label-row">
            <span>Sentiment</span>
            <strong style="color: ${getSentimentColor(turn.sentiment_after)};">${turn.sentiment_after.toFixed(2)}</strong>
          </div>
          <div class="slider-bar-track">
            <div class="slider-bar-fill fill-sentiment" style="width: ${sentimentVal}%; background: ${getSentimentColor(turn.sentiment_after)};"></div>
          </div>
        </div>
        <div class="live-slider-item">
          <div class="slider-label-row">
            <span>Conviction</span>
            <strong>${Math.round(convictionVal)}%</strong>
          </div>
          <div class="slider-bar-track">
            <div class="slider-bar-fill fill-conviction" style="width: ${convictionVal}%;"></div>
          </div>
        </div>
      </div>
    `;
  }
  
  let monologueHtml = '';
  if (turn.internal_monologue && turn.internal_monologue !== "Offline mock reaction.") {
    monologueHtml = `
      <div class="inner-monologue-accordion">
        <button class="monologue-trigger" onclick="toggleMonologue(this)">
          <i class="fa-solid fa-brain"></i> Toggle Inner Thoughts
        </button>
        <div class="monologue-content hidden">
          "${escapeHTML(turn.internal_monologue)}"
        </div>
      </div>
    `;
  }
  
  let correctionHtml = '';
  if (turn.factuality_score !== undefined) {
    const accuracyPercent = Math.round(turn.factuality_score * 100);
    const isValid = turn.is_factually_correct && turn.factuality_score >= 0.85;
    const alertClass = isValid ? 'valid' : 'invalid';
    const icon = isValid ? 'fa-circle-check' : 'fa-circle-exclamation';
    const title = isValid ? `Verified Stance (Accuracy: ${accuracyPercent}%)` : `Fact Check Warning (Accuracy: ${accuracyPercent}%)`;
    
    const messageText = isValid 
      ? `The statements and logic presented align with the Ground Truth Company Profile.`
      : (turn.moderator_note || "Significant factual or logical discrepancies were detected relative to the Company Profile.");
    
    correctionHtml = `
      <div class="fact-check-alert ${alertClass}">
        <i class="fa-solid ${icon}"></i>
        <div>
          <strong>${title}:</strong> ${escapeHTML(messageText)}
          ${turn.cited_source ? `
            <div class="fact-check-source" style="margin-top: 4px; font-size: 0.78rem; opacity: 0.95;">
              <i class="fa-solid fa-file-contract"></i> Verification Source: <span onclick="openVerificationModal(${turn.turn})" style="font-weight: 600; text-decoration: underline; cursor: pointer; color: var(--color-lavender);" role="button" tabindex="0">${escapeHTML(turn.cited_source)}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  } else if (turn.moderator_note) {
    const isValid = turn.is_factually_correct;
    const alertClass = isValid ? 'valid' : 'invalid';
    const icon = isValid ? 'fa-circle-check' : 'fa-circle-exclamation';
    const title = isValid ? 'Statement Fact-Checked' : 'Fact Check Warning';
    
    correctionHtml = `
      <div class="fact-check-alert ${alertClass}">
        <i class="fa-solid ${icon}"></i>
        <div>
          <strong>${title}:</strong> ${escapeHTML(turn.moderator_note)}
          ${turn.cited_source ? `
            <div class="fact-check-source" style="margin-top: 4px; font-size: 0.78rem; opacity: 0.95;">
              <i class="fa-solid fa-file-contract"></i> Verification Source: <span onclick="openVerificationModal(${turn.turn})" style="font-weight: 600; text-decoration: underline; cursor: pointer; color: var(--color-lavender);" role="button" tabindex="0">${escapeHTML(turn.cited_source)}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
  
  turnCard.innerHTML = `
    <div class="bubble-avatar ${escapeHTML(avatarClass)}">${escapeHTML(initialName)}</div>
    <div class="bubble-body">
      <div class="bubble-header">
        <div class="agent-name-role">
          <h3>${escapeHTML(turn.speaker)}</h3>
          <span class="agent-swarm-tag ${escapeHTML(swarmClass)}">${escapeHTML(swarmType)}</span>
        </div>
        <span class="bubble-turn">Turn #${turn.turn}</span>
      </div>
      
      ${slidersHtml}
      
      <p class="bubble-speech">${escapeHTML(turn.speech)}</p>
      
      ${monologueHtml}
      ${correctionHtml}
    </div>
  `;
  
  container.appendChild(turnCard);
  container.scrollTop = container.scrollHeight;
}

function updateTurnFactCheckInDOM(turn) {
  const card = document.querySelector(`[data-turn-number="${turn.turn}"]`);
  if (!card) return;
  
  const oldAlert = card.querySelector('.fact-check-alert');
  if (oldAlert) oldAlert.remove();
  
  let correctionHtml = '';
  if (turn.factuality_score !== undefined && turn.factuality_score !== null) {
    const accuracyPercent = Math.round(turn.factuality_score * 100);
    const isValid = turn.is_factually_correct && turn.factuality_score >= 0.85;
    const alertClass = isValid ? 'valid' : 'invalid';
    const icon = isValid ? 'fa-circle-check' : 'fa-circle-exclamation';
    const title = isValid ? `Verified Stance (Accuracy: ${accuracyPercent}%)` : `Fact Check Warning (Accuracy: ${accuracyPercent}%)`;
    
    const messageText = isValid 
      ? `The statements and logic presented align with the Ground Truth Company Profile.`
      : (turn.moderator_note || "Significant factual or logical discrepancies were detected relative to the Company Profile.");
 
    correctionHtml = `
      <div class="fact-check-alert ${alertClass}" style="animation: fadeIn 0.4s ease-out;">
        <i class="fa-solid ${icon}"></i>
        <div>
          <strong>${title}:</strong> ${escapeHTML(messageText)}
          ${turn.cited_source ? `
            <div class="fact-check-source" style="margin-top: 4px; font-size: 0.78rem; opacity: 0.95;">
              <i class="fa-solid fa-file-contract"></i> Verification Source: <span onclick="openVerificationModal(${turn.turn})" style="font-weight: 600; text-decoration: underline; cursor: pointer; color: var(--color-lavender);" role="button" tabindex="0">${escapeHTML(turn.cited_source)}</span>
            </div>
          ` : ''}
        </div>
      </div>
    `;
  }
  
  if (correctionHtml) {
    const body = card.querySelector('.bubble-body');
    if (body) {
      const tempDiv = document.createElement('div');
      tempDiv.innerHTML = correctionHtml;
      body.appendChild(tempDiv.firstElementChild);
    }
  }
}

function toggleMonologue(btn) {
  const content = btn.nextElementSibling;
  content.classList.toggle('hidden');
}

function renderConfigAgentsTable() {
  const tbody = document.getElementById('config-agents-tbody');
  tbody.innerHTML = '';
  
  Object.entries(activeAgents).forEach(([key, agent]) => {
    const shortType = agent.swarm_type.split(' ')[0];
    tbody.innerHTML += `
      <tr data-agent-key="${escapeHTML(key)}">
        <td style="font-weight: 600;">${escapeHTML(agent.name)}</td>
        <td><span class="agent-swarm-tag ${escapeHTML(getSwarmTypeClass(agent.swarm_type))}">${escapeHTML(shortType)}</span></td>
        <td>${parseFloat(agent.initial_sentiment).toFixed(1)}</td>
        <td>${Math.round(agent.initial_conviction * 100)}%</td>
        <td>${Math.round(agent.reactivity_threshold * 100)}%</td>
        <td>
          <button class="action-edit-btn" onclick="editAgentInForm(\`${escapeHTML(key.replace(/`/g, '\\`'))}\`)" title="Edit Agent"><i class="fa-solid fa-pen-to-square"></i></button>
          <button class="action-delete-btn" onclick="deleteAgentFromConfig(\`${escapeHTML(key.replace(/`/g, '\\`'))}\`)" title="Delete Agent"><i class="fa-solid fa-trash-can"></i></button>
        </td>
      </tr>
    `;
  });
}

function renderAgentEndStates() {
  const container = document.getElementById('agent-consensus-endstate');
  container.innerHTML = '';
  
  const stateHistory = simulationResult.state_tracking;
  const finalTurnState = stateHistory[stateHistory.length - 1].states;
  
  Object.entries(finalTurnState).forEach(([name, state]) => {
    const persona = personasData[name] || { swarm_type: "Retail & Consumer Swarm" };
    const swarmClass = getSwarmTypeClass(persona.swarm_type);
    const shortType = persona.swarm_type.split(' ')[0];
    
    const sentimentPct = ((state.sentiment + 1) / 2) * 100;
    const convictionPct = state.conviction * 100;
    
    let rating = 'Neutral';
    let ratingClass = 'swarm-structural';
    if (state.sentiment > 0.25) {
      rating = 'Bullish';
      ratingClass = 'swarm-retail';
    } else if (state.sentiment < -0.25) {
      rating = 'Bearish';
      ratingClass = 'swarm-analytical';
    }
    
    container.innerHTML += `
      <div class="agent-consensus-card">
        <div class="consensus-card-header">
          <h4>${escapeHTML(name)}</h4>
          <span class="${escapeHTML(ratingClass)}">${escapeHTML(rating)}</span>
        </div>
        
        <div class="consensus-slider-row">
          <div class="consensus-slider-label">
            <span>Sentiment</span>
            <strong>${state.sentiment.toFixed(2)}</strong>
          </div>
          <div class="slider-bar-track">
            <div class="slider-bar-fill fill-sentiment" style="width: ${sentimentPct}%;"></div>
          </div>
        </div>
        
        <div class="consensus-slider-row">
          <div class="consensus-slider-label">
            <span>Conviction</span>
            <strong>${Math.round(convictionPct)}%</strong>
          </div>
          <div class="slider-bar-track">
            <div class="slider-bar-fill fill-conviction" style="width: ${convictionPct}%;"></div>
          </div>
        </div>
      </div>
    `;
  });
}
