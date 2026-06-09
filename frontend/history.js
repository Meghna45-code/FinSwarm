// ==================== DEBATE HISTORY CONTROLS ====================

let historicalDebates = [];

async function loadHistory() {
  const loadingEl = document.getElementById('history-loading');
  const listEl = document.getElementById('history-list');
  
  loadingEl.classList.remove('hidden');
  listEl.innerHTML = '';
  
  try {
    historicalDebates = await apiGetDebates();
    renderHistoryList(historicalDebates);
  } catch (err) {
    console.error("Failed to load history:", err);
    listEl.innerHTML = `<div style="color: var(--color-red); padding: 12px; font-size: 0.85rem;">Failed to load history</div>`;
  } finally {
    loadingEl.classList.add('hidden');
  }
}

function renderHistoryList(debates) {
  const listEl = document.getElementById('history-list');
  listEl.innerHTML = '';
  
  if (debates.length === 0) {
    listEl.innerHTML = `<div style="color: var(--text-dark); padding: 16px; font-size: 0.85rem; text-align: center;">No debate history yet.</div>`;
    return;
  }
  
  debates.forEach(deb => {
    const card = document.createElement('div');
    card.className = 'agent-sidebar-card';
    card.style.position = 'relative';
    card.onclick = () => loadHistoricalDebate(deb.id);
    
    const dateStr = new Date(deb.created_at).toLocaleString();
    
    card.innerHTML = `
      <div class="agent-card-top">
        <h4 style="text-overflow: ellipsis; overflow: hidden; white-space: nowrap; max-width: 170px;">${escapeHTML(deb.company_name)}</h4>
        <span class="ticker-badge" style="font-size: 0.7rem; padding: 2px 6px;">${escapeHTML(deb.company_ticker)}</span>
      </div>
      <div class="agent-card-role" style="margin-top: 4px; font-size: 0.75rem; color: var(--text-muted); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">
        ${escapeHTML(deb.news_content)}
      </div>
      <div style="font-size: 0.65rem; color: var(--text-dark); margin-top: 6px;">
        <i class="fa-solid fa-clock" style="margin-right: 4px;"></i> ${dateStr}
      </div>
    `;
    listEl.appendChild(card);
  });
}

function filterHistory() {
  const query = document.getElementById('history-search-input').value.toLowerCase();
  const filtered = historicalDebates.filter(deb => 
    deb.company_name.toLowerCase().includes(query) ||
    deb.company_ticker.toLowerCase().includes(query) ||
    deb.news_content.toLowerCase().includes(query)
  );
  renderHistoryList(filtered);
}

async function loadHistoricalDebate(debateId) {
  try {
    const details = await apiGetDebateDetails(debateId);
    simulationResult = details;
    companyData = details.company_profile;
    renderCompanyProfile(companyData);
    
    // Set debate timeline news title
    document.getElementById('debate-running-news').textContent = details.news_content;
    document.getElementById('debate-news-impact').textContent = `${Math.round(details.news_analysis.impact * 100)}%`;
    document.getElementById('debate-news-sentiment').textContent = details.news_analysis.sentiment.toFixed(2);
    
    // Populate the timeline
    populateTimelineFromTranscript();
    
    // Render the final verdict
    renderFinalVerdict();
  } catch (err) {
    console.error("Error loading historical debate:", err);
    alert("Could not load debate details from history.");
  }
}

function populateTimelineFromTranscript() {
  const container = document.getElementById('debate-timeline-messages');
  container.innerHTML = '';
  if (simulationResult && simulationResult.transcript) {
    simulationResult.transcript.forEach(turn => {
      appendTurnToTimeline(turn);
      if (turn.moderator_note || !turn.is_factually_correct) {
        updateTurnFactCheckInDOM({
          turn: turn.turn,
          speaker: turn.speaker,
          is_factually_correct: turn.is_factually_correct,
          factuality_score: turn.factuality_score,
          moderator_note: turn.moderator_note,
          cited_source: turn.cited_source
        });
      }
    });
  }
}
