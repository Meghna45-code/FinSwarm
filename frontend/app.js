// ==================== APP STATE & VARIABLES ====================
let currentUser = null;
let currentTutorialSlide = 0;
let selectedMode = 'debate';
let currentView = 'silent'; // 'silent' (direct results), 'debate'
let simulationResult = null;
let personasData = {};
let defaultAgentsData = {};
let activeAgents = {};
let companyData = {};
let activeEnvironments = {};
let chartInstance = null;
let isRecording = false;
let recognition = null;
let mockVoiceTimeout1 = null;
let mockVoiceTimeout2 = null;
let attachedFileContent = null;
let attachedFileName = "";

// Playback and interactive simulation states
let currentNewsContent = "";
let isPlaybackPaused = false;
let currentPlaybackIndex = 0;
let playbackTimeoutId = null;
let uiPlaybackQueue = [];
let isProcessingQueue = false;
let streamFinished = false;
let shouldAutoSkipToVerdict = false;
let silentProgressInterval = null;
let silentFactInterval = null;
let silentProgressPercent = 0;

// Sliders manual override flags
let sentimentManuallySet = false;
let convictionManuallySet = false;
let reactivityManuallySet = false;

// PDF.js worker setup
if (typeof pdfjsLib !== 'undefined') {
  pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.4.120/pdf.worker.min.js';
}

// Default Fallback Facts
const DEFAULT_FALLBACK_FACTS = [
  "Reliance Industries Limited (RELIANCE.NS) is India's largest company by market capitalization (₹17.63 Trillion).",
  "Jio Platforms leads the Indian telecom sector with over 450 Million 5G subscribers and ARPU of ₹181.7.",
  "Reliance Retail operates India's largest retail network with over 18,000 nationwide store locations.",
  "The Dhirubhai Ambani Green Energy Complex in Jamnagar features a 40 GWh Kutch Battery Gigafactory and Green Hydrogen electrolyzer infrastructure.",
  "Reliance's Jamnagar refinery is the world's largest single-location petroleum refining complex processing 1.24 Million barrels per day."
];

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  initAuth();
  initTutorial();
  initChatInput();
  initVoiceRecognition();
  adjustFloatingEditControls();
  window.addEventListener('resize', adjustFloatingEditControls);
  setSimulationView('debate');
  // Auto-load Reliance Industries company profile at startup
  setTimeout(() => {
    const tickerInput = document.getElementById('ticker-search-input');
    if (tickerInput) {
      tickerInput.value = 'RELIANCE.NS';
      loadCustomTicker();
    } else {
      // ticker-search-input was removed, directly call the API
      apiGetCompanyProfile('RELIANCE.NS').then(profile => {
        companyData = profile;
        if (typeof renderCompanyProfile === 'function') renderCompanyProfile(companyData);
      }).catch(err => console.warn('Could not auto-load Reliance profile:', err));
    }
  }, 300);
});

// Auth Flow handlers have been moved to auth.js

// ==================== 2. TUTORIAL FLOW ====================
function initTutorial() {
  const prevBtn = document.getElementById('tutorial-prev-btn');
  const nextBtn = document.getElementById('tutorial-next-btn');
  const skipBtn = document.getElementById('tutorial-skip-btn');
  const closeBtn = document.getElementById('tutorial-close-btn');

  if (prevBtn) prevBtn.addEventListener('click', () => {
    if (currentTutorialSlide > 0) showTutorialSlide(currentTutorialSlide - 1);
  });
  if (nextBtn) nextBtn.addEventListener('click', () => {
    if (currentTutorialSlide < 3) showTutorialSlide(currentTutorialSlide + 1);
    else endTutorial();
  });
  if (skipBtn) skipBtn.addEventListener('click', endTutorial);
  if (closeBtn) closeBtn.addEventListener('click', endTutorial);

  document.querySelectorAll('.tutorial-dots .dot').forEach(dot => {
    dot.addEventListener('click', () => {
      showTutorialSlide(parseInt(dot.getAttribute('data-slide')));
    });
  });

  const navTutorialBtn = document.getElementById('nav-tutorial-btn');
  if (navTutorialBtn) {
    navTutorialBtn.addEventListener('click', () => {
      const ts = document.getElementById('tutorial-screen');
      if (ts) ts.classList.add('active');
      showTutorialSlide(0);
    });
  }

  const helpTutorialBtn = document.getElementById('help-tutorial-btn');
  if (helpTutorialBtn) {
    helpTutorialBtn.addEventListener('click', () => {
      const ts = document.getElementById('tutorial-screen');
      if (ts) ts.classList.add('active');
      showTutorialSlide(0);
    });
  }
}

function showTutorialSlide(index) {
  currentTutorialSlide = index;
  
  const slides = document.querySelectorAll('.tutorial-slide');
  slides.forEach(s => s.classList.remove('active'));
  document.querySelector(`.tutorial-slide[data-slide="${index}"]`).classList.add('active');
  
  const dots = document.querySelectorAll('.tutorial-dots .dot');
  dots.forEach(d => d.classList.remove('active'));
  document.querySelector(`.tutorial-dots .dot[data-slide="${index}"]`).classList.add('active');
  
  const prevBtn = document.getElementById('tutorial-prev-btn');
  const nextBtn = document.getElementById('tutorial-next-btn');
  
  prevBtn.disabled = index === 0;
  
  if (index === 3) {
    nextBtn.textContent = 'Get Started';
  } else {
    nextBtn.textContent = 'Next';
  }
}

function endTutorial() {
  document.getElementById('tutorial-screen').classList.remove('active');
  document.getElementById('main-screen').classList.add('active');
}

// ==================== 3. SIDEBAR DATA LOADING ====================

// Static fallback personas — used if /api/personas is unavailable at startup
const STATIC_FALLBACK_PERSONAS = {
  "Algorithmic Quantitative Trader": {
    name: "Algorithmic Quantitative Trader", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Cold, deterministic statistical arbitrage model operating with zero emotional capacity and 100% numerical precision.",
    initial_sentiment: 0.0, initial_conviction: 0.9, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.15, market_influence_weight: 0.35, social_influence_susceptibility: 0.0, risk_tolerance: 0.5, expertise_domains: []
  },
  "Institutional Value Investor": {
    name: "Institutional Value Investor", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Rational, long-term asset manager focused entirely on intrinsic DCF valuation, FCF sustainability, ROIC, and operating margin stability.",
    initial_sentiment: 0.1, initial_conviction: 0.8, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.5, market_influence_weight: 0.4, social_influence_susceptibility: 0.1, risk_tolerance: 0.2, expertise_domains: []
  },
  "Technical Day Trader": {
    name: "Technical Day Trader", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Active momentum trader monitoring price action, volume expansion, and breakout signals with aggressive short-term bias.",
    initial_sentiment: 0.3, initial_conviction: 0.75, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.2, market_influence_weight: 0.25, social_influence_susceptibility: 0.4, risk_tolerance: 0.8, expertise_domains: []
  },
  "Aggressive Short-Seller": {
    name: "Aggressive Short-Seller", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Adversarial research analyst hunting for overvaluation, leverage risk, and accounting red flags.",
    initial_sentiment: -0.5, initial_conviction: 0.85, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.3, market_influence_weight: 0.3, social_influence_susceptibility: 0.1, risk_tolerance: 0.9, expertise_domains: []
  },
  "Retail Momentum Chaser": {
    name: "Retail Momentum Chaser", swarm_type: "Retail & Consumer Swarm",
    role_identity: "Emotion-driven retail trader chasing momentum, viral narratives, and social media hype with high volatility sensitivity.",
    initial_sentiment: 0.4, initial_conviction: 0.6, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.1, market_influence_weight: 0.1, social_influence_susceptibility: 0.9, risk_tolerance: 0.9, expertise_domains: []
  },
  "Brand Skeptic": {
    name: "Brand Skeptic", swarm_type: "Retail & Consumer Swarm",
    role_identity: "Consumer-behavior analyst tracking brand health, customer loyalty metrics, and NPS trajectory.",
    initial_sentiment: -0.2, initial_conviction: 0.7, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.4, market_influence_weight: 0.15, social_influence_susceptibility: 0.5, risk_tolerance: 0.4, expertise_domains: []
  },
  "Company Insider / Employee": {
    name: "Company Insider / Employee", swarm_type: "Structural & Macro Swarm",
    role_identity: "Internal operational manager embedded within the company tracking day-to-day execution metrics and morale signals.",
    initial_sentiment: 0.15, initial_conviction: 0.8, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.35, market_influence_weight: 0.2, social_influence_susceptibility: 0.3, risk_tolerance: 0.3, expertise_domains: []
  },
  "Macro Economist": {
    name: "Macro Economist", swarm_type: "Structural & Macro Swarm",
    role_identity: "Top-down macroeconomic strategist assessing interest rate policy, GDP growth cycles, and inflation risk.",
    initial_sentiment: 0.0, initial_conviction: 0.85, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.3, market_influence_weight: 0.35, social_influence_susceptibility: 0.1, risk_tolerance: 0.3, expertise_domains: []
  },
  "Regulatory Compliance Watchdog": {
    name: "Regulatory Compliance Watchdog", swarm_type: "Structural & Macro Swarm",
    role_identity: "Legal and antitrust policy expert scrutinizing SEC/SEBI compliance, litigation exposure, and government policy shifts.",
    initial_sentiment: -0.1, initial_conviction: 0.8, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.25, market_influence_weight: 0.25, social_influence_susceptibility: 0.1, risk_tolerance: 0.2, expertise_domains: []
  },
  "Industry Tech Expert": {
    name: "Industry Tech Expert", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Deep-tech engineer and product architect assessing patent moat, R&D execution, and technical scalability.",
    initial_sentiment: 0.2, initial_conviction: 0.85, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.2, market_influence_weight: 0.3, social_influence_susceptibility: 0.2, risk_tolerance: 0.6, expertise_domains: []
  },
  "ESG Specialist": {
    name: "ESG Specialist", swarm_type: "Structural & Macro Swarm",
    role_identity: "Strict sustainability and governance analyst evaluating carbon emissions, renewable energy strategy, and board ethics.",
    initial_sentiment: 0.05, initial_conviction: 0.8, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.3, market_influence_weight: 0.2, social_influence_susceptibility: 0.3, risk_tolerance: 0.3, expertise_domains: []
  },
  "Dividend Growth Investor": {
    name: "Dividend Growth Investor", swarm_type: "Trading & Analytical Swarm",
    role_identity: "Highly conservative capital preservation investor assessing free cash flow coverage, dividend yield security, and debt service ratios.",
    initial_sentiment: 0.1, initial_conviction: 0.85, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.4, market_influence_weight: 0.3, social_influence_susceptibility: 0.1, risk_tolerance: 0.2, expertise_domains: []
  },
  "B2B Supply Chain Partner / Vanguard": {
    name: "B2B Supply Chain Partner / Vanguard", swarm_type: "Structural & Macro Swarm",
    role_identity: "Upstream supplier and logistics manager tracking raw material component costs, lead times, and inventory bottlenecks.",
    initial_sentiment: 0.0, initial_conviction: 0.75, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.3, market_influence_weight: 0.25, social_influence_susceptibility: 0.2, risk_tolerance: 0.4, expertise_domains: []
  },
  "Brand Loyalist / Fanboy": {
    name: "Brand Loyalist / Fanboy", swarm_type: "Retail & Consumer Swarm",
    role_identity: "Unconditionally bullish brand enthusiast celebrating corporate achievements, technological breakthroughs, and long-term expansion.",
    initial_sentiment: 0.6, initial_conviction: 0.9, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.1, market_influence_weight: 0.15, social_influence_susceptibility: 0.8, risk_tolerance: 0.85, expertise_domains: []
  },
  "Panic-Prone Retail Trader": {
    name: "Panic-Prone Retail Trader", swarm_type: "Retail & Consumer Swarm",
    role_identity: "Highly risk-averse retail investor prone to rapid sentiment swings, fear of drawdown, and emotional capitulation.",
    initial_sentiment: -0.3, initial_conviction: 0.7, primary_metrics: [], cognitive_biases: [], linguistic_style: "", good_news_reaction: "", bad_news_reaction: "", reactivity_threshold: 0.1, market_influence_weight: 0.1, social_influence_susceptibility: 0.95, risk_tolerance: 0.1, expertise_domains: []
  }
};

async function loadSidebarData() {
  try {
    // Load agents — company profile is loaded on-demand
    personasData = await apiGetPersonas();
    defaultAgentsData = JSON.parse(JSON.stringify(personasData));
    activeAgents = JSON.parse(JSON.stringify(personasData));
    renderAgentsList(personasData);

    companyData = {
      ticker: "RELIANCE.NS", name: "Reliance Industries Limited", sector: "Energy & Conglomerate",
      industry: "Oil & Gas, Telecom, Retail & New Energy", description: "India's largest company by market cap.",
      key_metrics: {"Market Cap": "₹17.63 Trillion", "Stock Price": "₹1,302.60"}, recent_events: [], historical_news: [], one_sentence_facts: DEFAULT_FALLBACK_FACTS
    };
  } catch (error) {
    console.warn("Backend unreachable — using static fallback personas:", error);
    // Use embedded personas so sidebar always populates cleanly
    personasData = JSON.parse(JSON.stringify(STATIC_FALLBACK_PERSONAS));
    defaultAgentsData = JSON.parse(JSON.stringify(personasData));
    activeAgents = JSON.parse(JSON.stringify(personasData));
    renderAgentsList(personasData);

    companyData = {
      ticker: "RELIANCE.NS", name: "Reliance Industries Limited", sector: "Energy & Conglomerate",
      industry: "Oil & Gas, Telecom, Retail & New Energy", description: "India's largest company by market cap.",
      key_metrics: {"Market Cap": "₹17.63 Trillion", "Stock Price": "₹1,302.60"}, recent_events: [], historical_news: [], one_sentence_facts: DEFAULT_FALLBACK_FACTS
    };

    // Silently retry fetching live personas after 2s (replaces static cards if server comes up)
    setTimeout(() => {
      apiGetPersonas().then(pData => {
        personasData = pData;
        defaultAgentsData = JSON.parse(JSON.stringify(personasData));
        activeAgents = JSON.parse(JSON.stringify(personasData));
        renderAgentsList(personasData);
      }).catch(() => { /* server still down — static personas already shown, no error banner needed */ });
    }, 2000);
  }
}


// ==================== 4. CHAT BAR CONTROLS ====================
function initChatInput() {
  const input = document.getElementById('chat-input');
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitSimulation();
    }
  });
}

function autoResizeTextarea(textarea) {
  textarea.style.height = 'auto';
  textarea.style.height = textarea.scrollHeight + 'px';
  adjustFloatingEditControls();
}

function adjustFloatingEditControls() {
  const chatBar = document.querySelector('.chat-input-bar');
  const floatingControls = document.querySelector('.floating-edit-controls');
  if (chatBar && floatingControls) {
    const height = chatBar.offsetHeight;
    floatingControls.style.bottom = (height + 12) + 'px';
  }
}

function setInputPrompt(cardElement) {
  const pEl = cardElement.querySelector('p');
  const promptText = pEl ? pEl.textContent.replace(/^"|"$/g, '') : '';
  const chatInput = document.getElementById('chat-input');
  if (chatInput && promptText) {
    chatInput.value = promptText;
    autoResizeTextarea(chatInput);
  }
  submitSimulation();
}

function toggleViewDropdown() {
  const vd = document.getElementById('view-dropdown');
  if (vd) vd.classList.toggle('hidden');
}

function setSimulationView(view) {
  currentView = view;
  selectedMode = view;

  const viewDropdown = document.getElementById('view-dropdown');
  if (viewDropdown) viewDropdown.classList.add('hidden');

  const dropdownOptions = document.querySelectorAll('#view-dropdown .dropdown-option');
  if (dropdownOptions.length) {
    dropdownOptions.forEach(opt => opt.classList.remove('active'));
    const activeOpt = document.querySelector(`#view-dropdown .dropdown-option[data-view="${view}"]`);
    if (activeOpt) activeOpt.classList.add('active');
  }

  const viewToggleBtn = document.getElementById('view-toggle-btn');
  const badge = document.getElementById('active-mode-badge');

  let label = 'Direct Results';
  let iconHtml = '<i class="fa-solid fa-bolt text-blue"></i>';

  if (view === 'debate') {
    label = 'Live Debate';
    iconHtml = '<i class="fa-solid fa-comments text-purple"></i>';
  }

  if (viewToggleBtn) viewToggleBtn.innerHTML = iconHtml;
  if (badge) badge.innerHTML = `${iconHtml} ${label} Mode`;

  // Viewport switching if a simulation has been loaded or run
  if (simulationResult) {
    const inlineControls = document.getElementById('debate-inline-controls');
    
    if (view === 'silent') {
      if (playbackTimeoutId) {
        clearTimeout(playbackTimeoutId);
        playbackTimeoutId = null;
      }
      isPlaybackPaused = true;
      if (inlineControls) inlineControls.classList.add('hidden');
      renderFinalVerdict();
    } else {
      showViewport('viewport-live-debate');
      if (inlineControls) inlineControls.classList.remove('hidden');
      
      const container = document.getElementById('debate-timeline-messages');
      if (container) {
        setTimeout(() => {
          container.scrollTop = container.scrollHeight;
        }, 50);
      }
    }
  }
}

function toggleAttachmentMenu() {
  const el = document.getElementById('attachment-menu');
  if (el) el.classList.toggle('hidden');
}

function triggerFileUploader() {
  const el = document.getElementById('attachment-menu');
  if (el) el.classList.add('hidden');
  const fu = document.getElementById('file-uploader');
  if (fu) fu.click();
}

async function handleFileSelection(event) {
  const file = event.target.files[0];
  if (!file) return;

  attachedFileName = file.name;
  attachedFileContent = null;

  const previewBar = document.getElementById('attachment-preview-bar');
  if (previewBar) previewBar.classList.remove('hidden');

  const isPdf = file.name.toLowerCase().endsWith('.pdf');
  const fileIcon = isPdf ? 'fa-file-pdf' : 'fa-file-lines';
  const fileSizeStr = (file.size / 1024).toFixed(1) + ' KB';

  previewBar.innerHTML = `
    <div class="attachment-pill">
      <i class="fa-solid ${fileIcon}"></i>
      <span>${escapeHTML(file.name)} (${fileSizeStr})</span>
    </div>
    <div class="attachment-status-text">
      <i class="fa-solid fa-spinner fa-spin"></i>
      <span>Extracting text...</span>
    </div>
    <button class="btn-remove-attachment" onclick="removeAttachedFile()" title="Remove file">
      <i class="fa-solid fa-xmark"></i>
    </button>
  `;

  try {
    if (isPdf) {
      attachedFileContent = await apiUploadPdf(file);
    } else {
      attachedFileContent = await new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(e);
        reader.readAsText(file);
      });
    }

    previewBar.innerHTML = `
      <div class="attachment-pill">
        <i class="fa-solid ${fileIcon}"></i>
        <span>${escapeHTML(file.name)} (${fileSizeStr})</span>
      </div>
      <div class="attachment-status-text status-success">
        <i class="fa-solid fa-circle-check"></i>
        <span>Extracted</span>
      </div>
      <button class="btn-remove-attachment" onclick="removeAttachedFile()" title="Remove file">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;
  } catch (err) {
    console.error("File extraction error:", err);
    previewBar.innerHTML = `
      <div class="attachment-pill">
        <i class="fa-solid ${fileIcon}"></i>
        <span>${escapeHTML(file.name)} (${fileSizeStr})</span>
      </div>
      <div class="attachment-status-text" style="color: var(--color-red);">
        <i class="fa-solid fa-circle-exclamation"></i>
        <span>Extraction Failed</span>
      </div>
      <button class="btn-remove-attachment" onclick="removeAttachedFile()" title="Remove file">
        <i class="fa-solid fa-xmark"></i>
      </button>
    `;
  }
}

function removeAttachedFile() {
  attachedFileContent = null;
  attachedFileName = "";
  const fu = document.getElementById('file-uploader');
  if (fu) fu.value = "";
  const previewBar = document.getElementById('attachment-preview-bar');
  if (previewBar) { previewBar.classList.add('hidden'); previewBar.innerHTML = ''; }
}

function handleMockAttachment(type) {
  const el = document.getElementById('attachment-menu');
  if (el) el.classList.add('hidden');
  const chatInput = document.getElementById('chat-input');
  let tag = '';
  
  if (type === 'document') tag = '[Attached: Document - SEC_10K_Annual_Report.pdf] ';
  if (type === 'link') tag = '[Attached: Link - https://bloomberg.com/news/tsla] ';
  if (type === 'image') tag = '[Attached: Screenshot - tsla_chart_breakout.png] ';
  
  chatInput.value = tag + chatInput.value;
  autoResizeTextarea(chatInput);
  chatInput.focus();
}

// ==================== 5. SIMULATION SUBMISSION & VIEW COORDINATION ====================
function showViewport(sectionId) {
  document.querySelectorAll('.viewport-section').forEach(sec => {
    sec.classList.remove('active');
  });
  document.getElementById(sectionId).classList.add('active');
}

async function submitSimulation() {
  const inputEl = document.getElementById('chat-input');
  let newsText = inputEl ? inputEl.value.trim() : "";

  // Check if a debate simulation is currently active
  const liveViewport = document.getElementById('viewport-live-debate');
  const isDebateLiveActive = liveViewport && liveViewport.classList.contains('active') && simulationResult !== null && !streamFinished;

  if (isDebateLiveActive && newsText) {
    // Inject news live into active debate feed
    const timeline = document.getElementById('debate-timeline-messages');
    if (timeline) {
      timeline.querySelectorAll('.debate-bubble').forEach(b => b.classList.remove('spotlight-active'));
      const banner = document.createElement('div');
      banner.className = 'fact-check-alert valid';
      banner.style.margin = '14px 0';
      banner.style.padding = '14px 18px';
      banner.style.background = 'rgba(129, 191, 183, 0.15)';
      banner.style.border = '1.5px solid var(--color-lavender)';
      banner.style.borderRadius = 'var(--radius-sm)';
      banner.innerHTML = `
        <i class="fa-solid fa-newspaper text-glowing" style="font-size: 1.2rem; color: var(--color-lavender);"></i>
        <div>
          <strong style="color: var(--color-lavender);">📰 BREAKING NEWS INJECTED INTO LIVE DEBATE:</strong>
          <p style="margin-top: 4px; font-size: 0.88rem; color: var(--text-main); line-height: 1.4;">"${escapeHTML(newsText)}"</p>
        </div>
      `;
      timeline.appendChild(banner);
      banner.scrollIntoView({ behavior: 'smooth', block: 'end' });
    }

    inputEl.value = '';
    autoResizeTextarea(inputEl);

    try {
      const debateId = (simulationResult && simulationResult.id) ? simulationResult.id : 'current_debate';
      apiInjectNews(debateId, newsText).catch(e => console.warn('Mid-debate news injection notice:', e));
    } catch (e) {
      console.warn('News injection failed:', e);
    }
    return;
  }
  
  if (!newsText) {
    newsText = "Reliance Industries abruptly delays the highly-anticipated $4 Billion Jio Platforms IPO, electing instead to divert ₹1.5 Lakh Crore in free cash flow to accelerate the immediate commissioning of its 40 GWh Kutch Battery Giga-factory and a massive AI Data Centre partnership with Meta in Jamnagar.";
  }
  
  currentNewsContent = newsText;
  
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  isPlaybackPaused = false;
  currentPlaybackIndex = 0;
  silentProgressPercent = 0;
  
  inputEl.value = '';
  autoResizeTextarea(inputEl);
  const attMenu = document.getElementById('attachment-menu');
  if (attMenu) attMenu.classList.add('hidden');
  if (document.getElementById('view-dropdown')) {
    document.getElementById('view-dropdown').classList.add('hidden');
  }
  
  // Always set up debate timeline metadata in the background
  const runningNewsEl = document.getElementById('debate-running-news');
  if (runningNewsEl) {
    runningNewsEl.textContent = newsText + (attachedFileName ? ` (Attached: ${attachedFileName})` : '');
  }
  document.getElementById('debate-timeline-messages').innerHTML = `
    <div class="sidebar-loader" style="margin: auto;">
      <div class="spinner"></div>
      <span>Moderator assessing news and compiling profiles...</span>
    </div>
  `;

  // Automatically open and expand Swarm Agents sidebar tab
  if (typeof switchSidebarTab === 'function') {
    switchSidebarTab('agents');
  }

  showViewport('viewport-live-debate');
  
  try {
    let finalNewsContent = newsText;
    if (attachedFileContent) {
      finalNewsContent += `\n\n=== ATTACHED SOURCE CONTEXT: ${attachedFileName} ===\n${attachedFileContent}`;
    }

    const response = await apiRunSimulation(finalNewsContent, 2, activeAgents, activeEnvironments);
    removeAttachedFile();

    await processSimulationStream(response, false);
  } catch (error) {
    console.error("Simulation API Error:", error);
    alert("Error executing swarm simulation. Make sure the backend server is running.");
    resetToWorkspace();
  }
}

function resetToWorkspace() {
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  if (silentProgressInterval) {
    clearInterval(silentProgressInterval);
    silentProgressInterval = null;
  }
  if (silentFactInterval) {
    clearInterval(silentFactInterval);
    silentFactInterval = null;
  }
  silentProgressPercent = 0;
  isPlaybackPaused = false;
  currentPlaybackIndex = 0;
  simulationResult = null;
  // Hide inline debate controls
  const inlineControls = document.getElementById('debate-inline-controls');
  if (inlineControls) inlineControls.classList.add('hidden');
  showViewport('viewport-empty');
}

// --- SILENT CONSENSUS LOADERS ---
function runSilentLoader() {
  if (silentProgressInterval) clearInterval(silentProgressInterval);
  if (silentFactInterval) clearInterval(silentFactInterval);

  const progressBar = document.getElementById('silent-progress-bar');
  const progressLabel = document.getElementById('silent-progress-label');
  
  let currentPercent = silentProgressPercent || 0;
  progressBar.style.width = `${currentPercent.toFixed(1)}%`;
  
  const fadedFactContainer = document.getElementById('silent-faded-facts-container');
  const fadedFactEl = document.getElementById('silent-faded-fact');
  const getLatestFacts = () => (companyData && companyData.one_sentence_facts && companyData.one_sentence_facts.length > 0) ? companyData.one_sentence_facts : DEFAULT_FALLBACK_FACTS;
  
  let factIdx = 0;
  const initialFacts = getLatestFacts();
  fadedFactEl.textContent = initialFacts[factIdx % initialFacts.length];
  if (fadedFactContainer) fadedFactContainer.style.opacity = 0.45;

  silentFactInterval = setInterval(() => {
    if (fadedFactContainer) fadedFactContainer.style.opacity = 0;
    setTimeout(() => {
      factIdx++;
      const currentFacts = getLatestFacts();
      fadedFactEl.textContent = currentFacts[factIdx % currentFacts.length];
      if (fadedFactContainer) fadedFactContainer.style.opacity = 0.45;
    }, 500);
  }, 3500);

  silentProgressInterval = setInterval(() => {
    if (simulationResult !== null && (streamFinished || uiPlaybackQueue.length === 0)) {
      clearInterval(silentProgressInterval);
      clearInterval(silentFactInterval);
      silentProgressInterval = null;
      silentFactInterval = null;
      silentProgressPercent = 0;
      progressBar.style.width = '100%';
      progressLabel.textContent = 'Rendering final results...';
      renderFinalVerdict();
    } else {
      if (currentPercent < 30) {
        currentPercent += Math.random() * 8 + 2;
      } else if (currentPercent < 60) {
        currentPercent += Math.random() * 4 + 1;
      } else if (currentPercent < 85) {
        currentPercent += Math.random() * 2 + 0.5;
      } else if (currentPercent < 95) {
        currentPercent += 0.2;
      }
      currentPercent = Math.min(95, currentPercent);
      silentProgressPercent = currentPercent;
      progressBar.style.width = `${currentPercent.toFixed(1)}%`;
      
      if (currentPercent < 25) {
        progressLabel.textContent = 'Extracting company profile...';
      } else if (currentPercent < 50) {
        progressLabel.textContent = 'Compiling background scenarios...';
      } else if (currentPercent < 75) {
        progressLabel.textContent = 'Gathering agent consensus...';
      } else {
        progressLabel.textContent = 'Computing future price projections...';
      }
    }
  }, 200);
}

// --- LIVE DEBATE RENDERING ---
function startLiveDebateRendering() {
  const container = document.getElementById('debate-timeline-messages');
  container.innerHTML = '';
  
  document.getElementById('debate-news-impact').textContent = `${Math.round(simulationResult.news_analysis.impact * 100)}%`;
  document.getElementById('debate-news-sentiment').textContent = simulationResult.news_analysis.sentiment.toFixed(2);
  
  isPlaybackPaused = false;
  currentPlaybackIndex = 0;
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  
  const pauseBtn = document.getElementById('btn-pause-debate');
  if (pauseBtn) {
    pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
    pauseBtn.disabled = false;
  }

  // Show inline debate controls in the chat bar
  const inlineControls = document.getElementById('debate-inline-controls');
  if (inlineControls) inlineControls.classList.remove('hidden');

  switchSidebarTab('agents');
  initLiveMonitorColumn();
  renderNextPlaybackTurn();
}

function renderNextPlaybackTurn() {
  if (isPlaybackPaused) return;
  
  const transcript = simulationResult.transcript;
  if (currentPlaybackIndex >= transcript.length) {
    const pauseBtn = document.getElementById('btn-pause-debate');
    if (pauseBtn) pauseBtn.disabled = true;
    const inlineControls = document.getElementById('debate-inline-controls');
    if (inlineControls) inlineControls.classList.add('hidden');
    renderFinalVerdict();
    return;
  }
  
  const turn = transcript[currentPlaybackIndex];
  appendTurnToTimeline(turn);
  
  const turnStatesObj = simulationResult.state_tracking.find(st => st.turn === turn.turn);
  if (turnStatesObj && turnStatesObj.states) {
    updateSidebarAgentsParameters(turnStatesObj.states);
    updateLiveMonitorColumn(turnStatesObj.states, turn.speaker);
  }
  
  currentPlaybackIndex++;
  
  if (isVoiceActive) {
    speakTurn(turn.speaker, turn.speech).then(() => {
      if (!isPlaybackPaused) {
        playbackTimeoutId = setTimeout(renderNextPlaybackTurn, 1000);
      }
    });
  } else {
    playbackTimeoutId = setTimeout(renderNextPlaybackTurn, 2500);
  }
}

function toggleDebatePause() {
  const btn = document.getElementById('btn-pause-debate');
  if (!btn) return;
  
  if (isPlaybackPaused) {
    isPlaybackPaused = false;
    btn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
    runUIPlaybackLoop();
  } else {
    isPlaybackPaused = true;
    btn.innerHTML = '<i class="fa-solid fa-play"></i> Resume';
    window.speechSynthesis.cancel();
    if (playbackTimeoutId) {
      clearTimeout(playbackTimeoutId);
      playbackTimeoutId = null;
    }
  }
}

function skipDebateToVerdict() {
  window.speechSynthesis.cancel();
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  isPlaybackPaused = false;

  // Hide inline debate controls immediately
  const inlineControls = document.getElementById('debate-inline-controls');
  if (inlineControls) inlineControls.classList.add('hidden');

  if (!streamFinished) {
    const container = document.getElementById('debate-timeline-messages');
    let skipLoader = document.getElementById('debate-skip-loader');
    if (!skipLoader) {
      skipLoader = document.createElement('div');
      skipLoader.id = 'debate-skip-loader';
      skipLoader.className = 'sidebar-loader';
      skipLoader.style.margin = '20px auto';
      skipLoader.innerHTML = `
        <div class="spinner"></div>
        <span>Collecting all remaining turns and computing consensus...</span>
      `;
      container.appendChild(skipLoader);
      container.scrollTop = container.scrollHeight;
    }
    shouldAutoSkipToVerdict = true;
  } else {
    renderFinalVerdict();
  }
}


async function resumeSimulation() {
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  isPlaybackPaused = false;
  
  const container = document.getElementById('debate-timeline-messages');
  const loaderDiv = document.createElement('div');
  loaderDiv.id = 'debate-resume-loader';
  loaderDiv.className = 'sidebar-loader';
  loaderDiv.style.margin = '20px auto';
  loaderDiv.innerHTML = `
    <div class="spinner"></div>
    <span>Swarm adapting to edits, recalculating remaining turns...</span>
  `;
  container.appendChild(loaderDiv);
  container.scrollTop = container.scrollHeight;
  
  let finalNewsContent = currentNewsContent;
  if (attachedFileContent) {
    finalNewsContent += `\n\n=== ATTACHED SOURCE CONTEXT: ${attachedFileName} ===\n${attachedFileContent}`;
  }
  
  try {
    const response = await apiResumeSimulation(
      finalNewsContent,
      2,
      activeAgents,
      activeEnvironments,
      simulationResult.transcript.slice(0, currentPlaybackIndex),
      simulationResult.state_tracking.slice(0, currentPlaybackIndex + 1)
    );
    
    await processSimulationStream(response, true);
  } catch (error) {
    console.error("Resume simulation error:", error);
    alert("Error resuming debate. Starting a new analysis instead.");
    resetToWorkspace();
  }
}

// --- STREAMING PARSER & UI QUEUE PLAYBACK ---
async function runUIPlaybackLoop() {
  if (isPlaybackPaused) return;

  if (uiPlaybackQueue.length === 0) {
    if (streamFinished) {
      if (selectedMode === 'verdict') {
        const skipLoader = document.getElementById('debate-skip-loader');
        if (skipLoader) skipLoader.remove();
        renderFinalVerdict();
      }
    } else {
      // Stream not done yet — wait briefly then check again
      playbackTimeoutId = setTimeout(runUIPlaybackLoop, 100);
    }
    return;
  }

  const event = uiPlaybackQueue.shift();

  if (event.type === 'turn') {
    const turn = event.data;

    const existingBubble = document.querySelector(`[data-turn-number="${turn.turn}"]`);
    if (!existingBubble) {
      appendTurnToTimeline(turn);
    }

    let turnStatesObj = simulationResult.state_tracking.find(st => st && st.turn === turn.turn);
    let turnStates = (turnStatesObj && turnStatesObj.states) ? turnStatesObj.states : null;

    if (!turnStates) {
      turnStates = {};
      Object.keys(activeAgents).forEach(k => {
        const a = activeAgents[k];
        turnStates[a.name || k] = {
          sentiment: parseFloat(a.initial_sentiment || 0.0),
          conviction: parseFloat(a.initial_conviction || 0.5)
        };
      });
      if (turn.speaker && turn.sentiment_after !== undefined) {
        turnStates[turn.speaker] = {
          sentiment: parseFloat(turn.sentiment_after),
          conviction: parseFloat(turn.conviction_after)
        };
        if (activeAgents[turn.speaker]) {
          activeAgents[turn.speaker].initial_sentiment = turn.sentiment_after;
          activeAgents[turn.speaker].initial_conviction = turn.conviction_after;
        }
      }
    }

    try { updateSidebarAgentsParameters(turnStates, turn.speaker); } catch(e) { console.warn('Sidebar update:', e); }
    try { updateLiveMonitorColumn(turnStates, turn.speaker); } catch(e) { console.warn('Monitor update:', e); }

    currentPlaybackIndex = turn.turn;

    if (isVoiceActive && currentView === 'debate') {
      try { await speakTurn(turn.speaker, turn.speech); } catch(err) { console.warn('Speech error:', err); }
      playbackTimeoutId = setTimeout(runUIPlaybackLoop, 500);
    } else {
      playbackTimeoutId = setTimeout(runUIPlaybackLoop, 1800);
    }

  } else if (event.type === 'fact_check') {
    const fc = event.data;
    try { updateTurnFactCheckInDOM(fc); } catch(e) { console.warn('FactCheck DOM error:', e); }
    if (fc.states) {
      try { updateSidebarAgentsParameters(fc.states, fc.speaker); } catch(e) {}
      try { updateLiveMonitorColumn(fc.states, fc.speaker); } catch(e) {}
    }
    // fact_check is instant — immediately process next item
    playbackTimeoutId = setTimeout(runUIPlaybackLoop, 0);
  }
}

async function processSimulationStream(response, isResume = false) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  
  // Full reset of playback state — prevents stale locks from previous debates
  streamFinished = false;
  shouldAutoSkipToVerdict = false;
  uiPlaybackQueue = [];
  isProcessingQueue = false;
  currentPlaybackIndex = 0;

  if (!isResume) {
    simulationResult = {
      news_analysis: { sentiment: 0.0, impact: 0.1, summary: "" },
      transcript: [],
      state_tracking: [],
      debate_summary: "",
      valuation: null,
      company_profile: null
    };
  }

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const resumeLoader = document.getElementById('debate-resume-loader');
      if (resumeLoader) resumeLoader.remove();

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith('data: ')) {
          const rawData = trimmed.substring(6);
          try {
            const event = JSON.parse(rawData);

            if (event.type === 'debate_id') {
              simulationResult.id = event.data;
            } else if (event.type === 'company_profile') {
              companyData = event.data;
              simulationResult.company_profile = companyData;
              renderCompanyProfile(companyData);
              
              // Immediately show the first fact of the new company in the loader
              const fadedFactEl = document.getElementById('silent-faded-fact');
              if (fadedFactEl && companyData.one_sentence_facts && companyData.one_sentence_facts.length > 0) {
                fadedFactEl.textContent = companyData.one_sentence_facts[0];
              }

              if (!isResume) {
                const container = document.getElementById('debate-timeline-messages');
                container.innerHTML = '';
                switchSidebarTab('agents');
                initLiveMonitorColumn();
                
                const pauseBtn = document.getElementById('btn-pause-debate');
                if (pauseBtn) {
                  pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
                  pauseBtn.disabled = false;
                }
                const inlineControls = document.getElementById('debate-inline-controls');
                if (inlineControls) {
                  if (currentView === 'debate') {
                    inlineControls.classList.remove('hidden');
                  } else {
                    inlineControls.classList.add('hidden');
                  }
                }

                // Kick off the playback loop — it will poll every 100ms until turns arrive
                if (playbackTimeoutId) clearTimeout(playbackTimeoutId);
                playbackTimeoutId = setTimeout(runUIPlaybackLoop, 200);
              }
            } else if (event.type === 'news_analysis') {
              simulationResult.news_analysis = event.data;
              document.getElementById('debate-news-impact').textContent = `${Math.round(event.data.impact * 100)}%`;
              document.getElementById('debate-news-sentiment').textContent = event.data.sentiment.toFixed(2);
            } else if (event.type === 'state_update') {
              simulationResult.state_tracking.push(event.data);
            } else if (event.type === 'turn') {
              simulationResult.transcript.push(event.data);
              if ((currentView === 'debate' || selectedMode === 'debate') && !shouldAutoSkipToVerdict) {
                uiPlaybackQueue.push(event);
              }
            } else if (event.type === 'fact_check') {
              const fc = event.data;
              const matchingTurn = simulationResult.transcript.find(t => t.turn === fc.turn);
              if (matchingTurn) {
                matchingTurn.moderator_note = fc.moderator_note;
                matchingTurn.is_factually_correct = fc.is_factually_correct;
                matchingTurn.factuality_score = fc.factuality_score;
                matchingTurn.cited_source = fc.cited_source;
              }

              const matchingState = simulationResult.state_tracking.find(st => st.turn === fc.turn);
              if (matchingState && fc.states) {
                matchingState.states = fc.states;
              }

              if ((currentView === 'debate' || selectedMode === 'debate') && !shouldAutoSkipToVerdict) {
                uiPlaybackQueue.push(event);
              }
            } else if (event.type === 'verdict') {
              simulationResult.debate_summary = event.data.debate_summary;
              simulationResult.valuation = event.data.valuation;
            } else if (event.type === 'error') {
              throw new Error(event.data);
            }
          } catch (err) {
            console.error("SSE parse error:", err);
          }
        }
      }
    }
  } catch (error) {
    console.error("Streaming error:", error);
    alert(`Simulation failed: ${error.message}`);
    resetToWorkspace();
    return;
  }

  streamFinished = true;
  
  if (shouldAutoSkipToVerdict) {
    const skipLoader = document.getElementById('debate-skip-loader');
    if (skipLoader) skipLoader.remove();
    renderFinalVerdict();
  } else if (currentView === 'debate' || selectedMode === 'debate') {
    runUIPlaybackLoop();
  }
}

function renderFinalVerdict() {
  showViewport('viewport-final-verdict');

  const badge = document.getElementById('active-mode-badge');
  if (badge) {
    badge.innerHTML = `<i class="fa-solid fa-chart-line text-blue"></i> Swarm Verdict Concluded`;
  }
  
  const val = (simulationResult && simulationResult.valuation) ? simulationResult.valuation : null;
  if (!val) {
    console.error("Valuation data is missing from simulation result.");
    document.getElementById('verdict-current-price').textContent = "$0.00";
    document.getElementById('verdict-projected-price').textContent = "$0.00";
    const changeEl = document.getElementById('verdict-change-percent');
    if (changeEl) {
      changeEl.textContent = "+0.00%";
      changeEl.className = "val-value";
    }
    const summaryEl = document.getElementById('verdict-summary-text');
    if (summaryEl) {
      summaryEl.textContent = (simulationResult && simulationResult.debate_summary) || "Valuation model could not be computed.";
    }
    return;
  }
  
  const currentPrice = (val.current_price != null) ? Number(val.current_price) : 0;
  const projectedPrice = (val.final_projected_price != null) ? Number(val.final_projected_price) : 0;
  const pctChange = (val.price_change_percent != null) ? Number(val.price_change_percent) : 0;

  // Use ₹ symbol for Indian stocks, $ for others
  const ticker = (companyData && companyData.ticker) || '';
  const currencySymbol = (ticker.includes('.NS') || ticker.includes('.BO') || ticker.includes('BSE')) ? '₹' : '$';

  document.getElementById('verdict-current-price').textContent = `${currencySymbol}${currentPrice.toFixed(2)}`;
  document.getElementById('verdict-projected-price').textContent = `${currencySymbol}${projectedPrice.toFixed(2)}`;
  
  const changeEl = document.getElementById('verdict-change-percent');
  if (changeEl) {
    changeEl.textContent = `${pctChange > 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
    if (pctChange >= 0) {
      changeEl.className = "val-value text-glowing-green";
    } else {
      changeEl.className = "val-value text-glowing-red";
    }
  }
  
  const summaryEl = document.getElementById('verdict-summary-text');
  if (summaryEl) {
    summaryEl.textContent = simulationResult.debate_summary;
  }
  
  renderChart(val.historical_prices, val.projected_prices);
  if (typeof renderSwarmSentimentChart === 'function' && simulationResult.transcript) {
    renderSwarmSentimentChart(simulationResult.transcript);
  }
  renderAgentEndStates();
}

/**
 * Switches between Mode 1 (Live Debate Stream) and Mode 2 (Final Analysis & Graphs)
 * @param {'debate' | 'verdict'} mode 
 */
function switchWorkspaceMode(mode) {
  selectedMode = mode;
  currentView = mode;
  const debateBtn = document.getElementById('btn-workspace-mode-debate');
  const verdictBtn = document.getElementById('btn-workspace-mode-verdict');
  const activeBadge = document.getElementById('active-mode-badge');

  if (mode === 'debate') {
    if (debateBtn) { debateBtn.classList.add('active', 'btn-primary'); debateBtn.classList.remove('btn-outline'); }
    if (verdictBtn) { verdictBtn.classList.remove('active', 'btn-primary'); verdictBtn.classList.add('btn-outline'); }
    if (activeBadge) activeBadge.innerHTML = '<i class="fa-solid fa-comments"></i> Live Debate Stream';
    showViewport('viewport-live-debate');
  } else if (mode === 'verdict') {
    if (verdictBtn) { verdictBtn.classList.add('active', 'btn-primary'); verdictBtn.classList.remove('btn-outline'); }
    if (debateBtn) { debateBtn.classList.remove('active', 'btn-primary'); debateBtn.classList.add('btn-outline'); }
    if (activeBadge) activeBadge.innerHTML = '<i class="fa-solid fa-chart-line"></i> Final Analysis &amp; Graphs';
    
    // Synchronously switch screen layout IMMEDIATELY
    showViewport('viewport-final-verdict');

    // Populate baseline Reliance valuation synchronously if empty so screen renders 0ms
    if (!simulationResult || !simulationResult.valuation) {
      simulationResult = {
        id: "deb_master_reliance_30turns",
        news_analysis: { sentiment: -0.15, impact: 0.92, summary: "Reliance Industries 4-Step Sovereign Pivot (IPO Delay, Giga-factory & Meta AI Partnership)" },
        company_profile: {
          ticker: "RELIANCE.NS",
          name: "Reliance Industries Limited",
          sector: "Energy & Conglomerate",
          industry: "Oil & Gas, Telecom, Retail & New Energy",
          description: "India's largest company by market cap (₹17.63 Trillion)."
        },
        transcript: [],
        state_tracking: [],
        debate_summary: "The Swarm concludes that Reliance's ₹1.5 Lakh Crore CapEx diversion into clean energy battery gigafactories and Meta AI infrastructure creates long-term structural value, outstripping short-term Jio IPO delay volatility.",
        valuation: {
          ticker: "RELIANCE.NS",
          current_price: 1302.6,
          final_projected_price: 1425.80,
          price_change_percent: 9.46,
          dcf_intrinsic_value: 1450.00,
          wacc: 0.0765,
          verdict_action: "BULLISH / ACCUMULATE",
          historical_prices: [1210.5, 1225.0, 1240.0, 1235.0, 1250.0, 1270.0, 1265.0, 1280.0, 1295.0, 1290.0, 1310.0, 1305.0, 1302.6],
          projected_prices: [1302.6, 1320.0, 1345.5, 1370.0, 1395.0, 1410.0, 1425.8]
        }
      };
    }
    
    renderFinalVerdict();

    if (typeof loadMasterDebateSession === 'function') {
      loadMasterDebateSession().then(() => {
        renderFinalVerdict();
      });
    }
  }
}

window.switchWorkspaceMode = switchWorkspaceMode;

// Debate history loaders and controls have been moved to history.js

function handleTickerSearchKey(event) {
  if (event.key === 'Enter') {
    event.preventDefault();
    loadCustomTicker();
  }
}

async function loadCustomTicker() {
  const searchInput = document.getElementById('ticker-search-input');
  const query = searchInput.value.trim();
  if (!query) {
    alert("Please enter a company ticker or name (e.g. AAPL, Tesla, Google).");
    return;
  }

  // Send the raw query — the backend LLM resolves both ticker symbols AND company names
  const ticker = query;

  const loadingEl = document.getElementById('company-loading');
  const profileEl = document.getElementById('company-profile-view');
  const emptyState = document.getElementById('company-empty-state');

  loadingEl.classList.remove('hidden');
  loadingEl.innerHTML = `<div class="spinner"></div><span>Loading ${escapeHTML(query)} profile...</span>`;
  profileEl.classList.add('hidden');
  if (emptyState) emptyState.style.display = 'none';

  try {
    const profile = await apiGetCompanyProfile(ticker);
    companyData = profile;
    renderCompanyProfile(companyData);

    // Contextualize the swarm to align with the new company
    loadingEl.innerHTML = `<div class="spinner"></div><span>Aligning swarm to ${escapeHTML(query)}...</span>`;
    try {
      const adjustedPersonas = await apiContextualizePersonas(activeEnvironments, companyData);
      activeAgents = adjustedPersonas;
      renderAgentsList(activeAgents);
    } catch (err) {
      console.warn("LLM alignment failed, keeping current agents:", err);
    }
  } catch (error) {
    console.error(`Error loading company "${query}":`, error);
    alert(`Could not load profile for "${query}". Please check the name or ticker and try again.`);
    profileEl.classList.add('hidden');
    if (emptyState) emptyState.style.display = '';
    renderCompanyProfile(companyData);
  } finally {
    loadingEl.classList.add('hidden');
  }
}


