// ==================== VOICE INPUT & SPEECH RECOGNITION ====================

/**
 * Initializes HTML5 Web Speech API client.
 */
function initVoiceRecognition() {
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onstart = () => {
      isRecording = true;
      document.getElementById('voice-overlay').classList.add('active');
      document.getElementById('voice-overlay-transcript').textContent = 'Listening... Say something!';
    };
    
    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      stopVoiceInput(false);
    };
    
    recognition.onend = () => {
      isRecording = false;
      document.getElementById('voice-overlay').classList.remove('active');
    };
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      const chatInput = document.getElementById('chat-input');
      chatInput.value += (chatInput.value ? ' ' : '') + transcript;
      autoResizeTextarea(chatInput);
    };
  }
}

/**
 * Toggles verbal speech recording session.
 */
function toggleVoiceInput() {
  if (isRecording) {
    stopVoiceInput(true);
    return;
  }
  
  if (recognition) {
    try {
      recognition.start();
    } catch (e) {
      console.warn("Recognition already running:", e);
    }
  } else {
    // Fallback: Simulate voice recording if microphone is blocked or not supported
    simulateVoiceTyping();
  }
}

/**
 * Halts ongoing speech recognition.
 */
function stopVoiceInput(save = true) {
  if (recognition) {
    recognition.stop();
  }
  if (mockVoiceTimeout1) {
    clearTimeout(mockVoiceTimeout1);
    mockVoiceTimeout1 = null;
  }
  if (mockVoiceTimeout2) {
    clearTimeout(mockVoiceTimeout2);
    mockVoiceTimeout2 = null;
  }
  document.getElementById('voice-overlay').classList.remove('active');
  isRecording = false;
}

/**
 * Simulates transcription using text increments when offline or Speech API is unsupported.
 */
function simulateVoiceTyping() {
  isRecording = true;
  const overlay = document.getElementById('voice-overlay');
  const text = document.getElementById('voice-overlay-transcript');
  const chatInput = document.getElementById('chat-input');
  
  overlay.classList.add('active');
  text.textContent = 'Listening (Mock System)...';
  
  const mockPrompts = [
    "Analyze Tesla's upcoming factory expansion plans and how it affects short-term margins.",
    "Tesla faces trade restrictions in Germany gigafactory, look at consumer feedback.",
    "Analyze the structural risk of self-driving regulation delays in China."
  ];
  
  const chosenPrompt = mockPrompts[Math.floor(Math.random() * mockPrompts.length)];
  
  mockVoiceTimeout1 = setTimeout(() => {
    text.textContent = `Transcribing: "${chosenPrompt}"`;
    mockVoiceTimeout2 = setTimeout(() => {
      chatInput.value += (chatInput.value ? ' ' : '') + chosenPrompt;
      autoResizeTextarea(chatInput);
      overlay.classList.remove('active');
      isRecording = false;
    }, 1500);
  }, 2000);
}
