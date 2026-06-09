// ==================== APP STATE & VARIABLES ====================
let currentUser = null;
let currentTutorialSlide = 0;
let selectedMode = 'debate'; // 'debate', 'silent'
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
  "Swarm intelligence uses decentralized systems to reach optimal consensus valuations.",
  "The platform tracks 4 dynamic agent variables: Sentiment, Conviction, Reactivity, and Persuasion.",
  "Moderator agents fact-check statements and penalize falsified information automatically.",
  "Valuation Model projects price paths based on the global conviction and stance of 14 agents."
];

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  initAuth();
  initTutorial();
  initChatInput();
  initVoiceRecognition();
});

// Auth Flow handlers have been moved to auth.js

// ==================== 2. TUTORIAL FLOW ====================
function initTutorial() {
  const prevBtn = document.getElementById('tutorial-prev-btn');
  const nextBtn = document.getElementById('tutorial-next-btn');
  const skipBtn = document.getElementById('tutorial-skip-btn');
  const closeBtn = document.getElementById('tutorial-close-btn');
  
  const dots = document.querySelectorAll('.tutorial-dots .dot');
  
  prevBtn.addEventListener('click', () => {
    if (currentTutorialSlide > 0) {
      showTutorialSlide(currentTutorialSlide - 1);
    }
  });
  
  nextBtn.addEventListener('click', () => {
    if (currentTutorialSlide < 3) {
      showTutorialSlide(currentTutorialSlide + 1);
    } else {
      endTutorial();
    }
  });
  
  skipBtn.addEventListener('click', endTutorial);
  closeBtn.addEventListener('click', endTutorial);
  
  dots.forEach(dot => {
    dot.addEventListener('click', () => {
      const slideIndex = parseInt(dot.getAttribute('data-slide'));
      showTutorialSlide(slideIndex);
    });
  });

  document.getElementById('nav-tutorial-btn').addEventListener('click', () => {
    document.getElementById('tutorial-screen').classList.add('active');
    showTutorialSlide(0);
  });
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
async function loadSidebarData() {
  try {
    // Load agents only — company profile is loaded on-demand by the user
    personasData = await apiGetPersonas();
    defaultAgentsData = JSON.parse(JSON.stringify(personasData));
    activeAgents = JSON.parse(JSON.stringify(personasData));
    renderAgentsList(personasData);

    // Keep a lightweight default company for internal simulation use
    companyData = {
      ticker: "TSLA", name: "Tesla Inc", sector: "Consumer Cyclical",
      industry: "Auto Manufacturers", description: "Electric vehicle and clean energy company.",
      key_metrics: {}, recent_events: [], historical_news: [], one_sentence_facts: []
    };
  } catch (error) {
    console.error("Error loading sidebar data:", error);
    const agentsList = document.getElementById('agents-list');
    if (agentsList) {
      agentsList.innerHTML = `
        <div style="text-align:center;color:var(--color-red);padding:16px;font-size:0.82rem;display:flex;flex-direction:column;gap:10px;align-items:center;">
          <i class="fa-solid fa-triangle-exclamation" style="font-size:1.4rem;"></i>
          <span>Connection to backend failed. Make sure the API server is running.</span>
          <button class="btn btn-outline btn-sm" onclick="loadSidebarData()">
            <i class="fa-solid fa-arrows-rotate"></i> Retry
          </button>
        </div>
      `;
    }
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
}

function setInputPrompt(cardElement) {
  const promptText = cardElement.querySelector('p').textContent.replace(/"/g, '');
  const chatInput = document.getElementById('chat-input');
  chatInput.value = promptText;
  autoResizeTextarea(chatInput);
  chatInput.focus();
}

function toggleModeDropdown() {
  document.getElementById('mode-dropdown').classList.toggle('hidden');
}

function setSimulationMode(mode) {
  selectedMode = mode;
  document.getElementById('mode-dropdown').classList.add('hidden');
  
  document.querySelectorAll('.dropdown-option').forEach(opt => {
    opt.classList.remove('active');
  });
  document.querySelector(`.dropdown-option[data-mode="${mode}"]`).classList.add('active');
  
  const indicator = document.getElementById('mode-bubble');
  const badge = document.getElementById('active-mode-badge');
  
  let label = 'Live Debate';
  let iconHtml = '<i class="fa-solid fa-comments"></i>';
  
  if (mode === 'silent') {
    label = 'Silent Consensus';
    iconHtml = '<i class="fa-solid fa-bolt text-blue"></i>';
  }
  
  indicator.innerHTML = `${iconHtml} <span>${label}</span>`;
  badge.innerHTML = `${iconHtml} ${label} Mode`;
}

function toggleAttachmentMenu() {
  document.getElementById('attachment-menu').classList.toggle('hidden');
}

function triggerFileUploader() {
  document.getElementById('attachment-menu').classList.add('hidden');
  document.getElementById('file-uploader').click();
}

async function handleFileSelection(event) {
  const file = event.target.files[0];
  if (!file) return;

  attachedFileName = file.name;
  attachedFileContent = null;

  const previewBar = document.getElementById('attachment-preview-bar');
  previewBar.classList.remove('hidden');

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
  document.getElementById('file-uploader').value = "";
  const previewBar = document.getElementById('attachment-preview-bar');
  previewBar.classList.add('hidden');
  previewBar.innerHTML = '';
}

function handleMockAttachment(type) {
  document.getElementById('attachment-menu').classList.add('hidden');
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
  const newsText = inputEl.value.trim();
  
  if (!newsText) {
    alert("Please enter a financial headline or paste news first.");
    return;
  }
  
  currentNewsContent = newsText;
  
  if (playbackTimeoutId) {
    clearTimeout(playbackTimeoutId);
    playbackTimeoutId = null;
  }
  isPlaybackPaused = false;
  currentPlaybackIndex = 0;
  
  inputEl.value = '';
  autoResizeTextarea(inputEl);
  simulationResult = null;
  
  document.getElementById('attachment-menu').classList.add('hidden');
  document.getElementById('mode-dropdown').classList.add('hidden');
  
  if (selectedMode === 'silent') {
    showViewport('viewport-silent-consensus');
    runSilentLoader();
  } else {
    showViewport('viewport-live-debate');
    document.getElementById('debate-running-news').textContent = newsText + (attachedFileName ? ` (Attached: ${attachedFileName})` : '');
    document.getElementById('debate-timeline-messages').innerHTML = `
      <div class="sidebar-loader" style="margin: auto;">
        <div class="spinner"></div>
        <span>Moderator assessing news and compiling profiles...</span>
      </div>
    `;
  }
  
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
  isPlaybackPaused = false;
  currentPlaybackIndex = 0;
  simulationResult = null;
  showViewport('viewport-empty');
}

// --- SILENT CONSENSUS LOADERS ---
function runSilentLoader() {
  const progressBar = document.getElementById('silent-progress-bar');
  const progressLabel = document.getElementById('silent-progress-label');
  progressBar.style.width = '0%';
  
  const fadedFactContainer = document.getElementById('silent-faded-facts-container');
  const fadedFactEl = document.getElementById('silent-faded-fact');
  const facts = (companyData && companyData.one_sentence_facts) || DEFAULT_FALLBACK_FACTS;
  
  let factIdx = 0;
  fadedFactEl.textContent = facts[factIdx % facts.length];
  if (fadedFactContainer) fadedFactContainer.style.opacity = 0.45;

  const factInterval = setInterval(() => {
    if (fadedFactContainer) fadedFactContainer.style.opacity = 0;
    setTimeout(() => {
      factIdx++;
      fadedFactEl.textContent = facts[factIdx % facts.length];
      if (fadedFactContainer) fadedFactContainer.style.opacity = 0.45;
    }, 500);
  }, 3500);

  let currentPercent = 0;
  const progressInterval = setInterval(() => {
    if (simulationResult !== null && streamFinished) {
      clearInterval(progressInterval);
      clearInterval(factInterval);
      progressBar.style.width = '100%';
      progressLabel.textContent = 'Rendering final results...';
      setTimeout(() => {
        renderFinalVerdict();
      }, 600);
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
  
  switchSidebarTab('agents');
  initLiveMonitorColumn();
  renderNextPlaybackTurn();
}

function renderNextPlaybackTurn() {
  if (isPlaybackPaused) return;
  
  const transcript = simulationResult.transcript;
  if (currentPlaybackIndex >= transcript.length) {
    const container = document.getElementById('debate-timeline-messages');
    const transitionDiv = document.createElement('div');
    transitionDiv.className = 'verdict-footer-controls';
    transitionDiv.style.animation = 'fadeIn 0.5s ease-out';
    transitionDiv.innerHTML = `
      <button class="btn btn-primary" onclick="renderFinalVerdict()">
        <i class="fa-solid fa-chart-pie"></i> View Final Swarm Verdict & Projections
      </button>
    `;
    container.appendChild(transitionDiv);
    container.scrollTop = container.scrollHeight;
    
    const pauseBtn = document.getElementById('btn-pause-debate');
    if (pauseBtn) pauseBtn.disabled = true;
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
  if (isProcessingQueue) return;
  
  if (uiPlaybackQueue.length === 0) {
    if (streamFinished) {
      const skipLoader = document.getElementById('debate-skip-loader');
      if (skipLoader) skipLoader.remove();
      
      if (shouldAutoSkipToVerdict) {
        renderFinalVerdict();
        return;
      }
      
      const container = document.getElementById('debate-timeline-messages');
      if (container && !container.querySelector('.btn-primary i.fa-chart-pie')) {
        const transitionDiv = document.createElement('div');
        transitionDiv.className = 'verdict-footer-controls';
        transitionDiv.style.animation = 'fadeIn 0.5s ease-out';
        transitionDiv.innerHTML = `
          <button class="btn btn-primary" onclick="renderFinalVerdict()">
            <i class="fa-solid fa-chart-pie"></i> View Final Swarm Verdict & Projections
          </button>
        `;
        container.appendChild(transitionDiv);
        container.scrollTop = container.scrollHeight;
        
        const pauseBtn = document.getElementById('btn-pause-debate');
        if (pauseBtn) {
          pauseBtn.disabled = true;
        }
      }
    }
    return;
  }

  isProcessingQueue = true;
  const event = uiPlaybackQueue.shift();

  if (event.type === 'turn') {
    const turn = event.data;
    
    const existingBubble = document.querySelector(`[data-turn-number="${turn.turn}"]`);
    if (!existingBubble) {
      appendTurnToTimeline(turn);
    }
    
    const turnStatesObj = simulationResult.state_tracking.find(st => st.turn === turn.turn);
    if (turnStatesObj && turnStatesObj.states) {
      updateSidebarAgentsParameters(turnStatesObj.states);
      updateLiveMonitorColumn(turnStatesObj.states, turn.speaker);
    }
    
    currentPlaybackIndex = turn.turn;

    if (isVoiceActive) {
      try {
        await speakTurn(turn.speaker, turn.speech);
      } catch (err) {
        console.error("Speech playback error:", err);
      }
      await new Promise(resolve => setTimeout(resolve, 800));
    } else {
      await new Promise(resolve => setTimeout(resolve, 2200));
    }
  } else if (event.type === 'fact_check') {
    const fc = event.data;
    updateTurnFactCheckInDOM(fc);
    
    if (fc.states) {
      updateSidebarAgentsParameters(fc.states);
      updateLiveMonitorColumn(fc.states, fc.speaker);
    }
  }

  isProcessingQueue = false;
  runUIPlaybackLoop();
}

async function processSimulationStream(response, isResume = false) {
  const reader = response.body.getReader();
  const decoder = new TextDecoder('utf-8');
  let buffer = '';
  
  streamFinished = false;
  shouldAutoSkipToVerdict = false;
  uiPlaybackQueue = [];
  isProcessingQueue = false;

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
              
              if (selectedMode === 'debate' && !isResume) {
                const container = document.getElementById('debate-timeline-messages');
                container.innerHTML = '';
                switchSidebarTab('agents');
                initLiveMonitorColumn();
                
                const pauseBtn = document.getElementById('btn-pause-debate');
                if (pauseBtn) {
                  pauseBtn.innerHTML = '<i class="fa-solid fa-pause"></i> Pause';
                  pauseBtn.disabled = false;
                }
              }
            } else if (event.type === 'news_analysis') {
              simulationResult.news_analysis = event.data;
              if (selectedMode === 'debate') {
                document.getElementById('debate-news-impact').textContent = `${Math.round(event.data.impact * 100)}%`;
                document.getElementById('debate-news-sentiment').textContent = event.data.sentiment.toFixed(2);
              }
            } else if (event.type === 'state_update') {
              simulationResult.state_tracking.push(event.data);
            } else if (event.type === 'turn') {
              simulationResult.transcript.push(event.data);
              if (selectedMode === 'debate' && !shouldAutoSkipToVerdict) {
                uiPlaybackQueue.push(event);
                runUIPlaybackLoop();
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

              if (selectedMode === 'debate' && !shouldAutoSkipToVerdict) {
                uiPlaybackQueue.push(event);
                runUIPlaybackLoop();
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
  } else if (selectedMode === 'debate') {
    runUIPlaybackLoop();
  }
}

// --- FINAL VERDICT PAGE ---
function renderFinalVerdict() {
  showViewport('viewport-final-verdict');
  
  const val = simulationResult.valuation;
  
  document.getElementById('verdict-current-price').textContent = `$${val.current_price.toFixed(2)}`;
  document.getElementById('verdict-projected-price').textContent = `$${val.final_projected_price.toFixed(2)}`;
  
  const pctChange = val.price_change_percent;
  const changeEl = document.getElementById('verdict-change-percent');
  changeEl.textContent = `${pctChange > 0 ? '+' : ''}${pctChange.toFixed(2)}%`;
  
  if (pctChange >= 0) {
    changeEl.className = "val-value text-glowing-green";
  } else {
    changeEl.className = "val-value text-glowing-red";
  }
  
  document.getElementById('verdict-summary-text').textContent = simulationResult.debate_summary;
  
  renderChart(val.historical_prices, val.projected_prices);
  renderAgentEndStates();
}

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
    alert("Please enter a company ticker or name (e.g. AAPL, Tesla).");
    return;
  }

  // Convert query to a ticker-like string (strip spaces)
  const ticker = query.toUpperCase().replace(/\s+/g, '');

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
    console.error(`Error loading ticker ${ticker}:`, error);
    alert(`Could not load profile for "${query}". Try a ticker symbol like AAPL, MSFT, or TSLA.`);
    profileEl.classList.add('hidden');
    if (emptyState) emptyState.style.display = '';
    renderCompanyProfile(companyData);
  } finally {
    loadingEl.classList.add('hidden');
  }
}


