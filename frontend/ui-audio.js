// ==================== AUDIO / TEXT-TO-SPEECH CONTROLLER ====================

// Global speech synthesis configuration
let isVoiceActive = false; // Track TTS active state

function toggleVoiceSpeech() {
  isVoiceActive = !isVoiceActive;
  const toggleBtn = document.getElementById('btn-voice-toggle');
  if (isVoiceActive) {
    toggleBtn.innerHTML = '<i class="fa-solid fa-volume-high text-glowing"></i> Voice On';
    toggleBtn.classList.add('btn-primary');
    toggleBtn.classList.remove('btn-outline');
  } else {
    toggleBtn.innerHTML = '<i class="fa-solid fa-volume-xmark"></i> Voice Speak';
    toggleBtn.classList.remove('btn-primary');
    toggleBtn.classList.add('btn-outline');
    window.speechSynthesis.cancel(); // Cancel any speaking instantly
  }
}

/**
 * Speak a turn using HTML5 SpeechSynthesis.
 * Returns a Promise that resolves when speech completes, so playback can sync correctly.
 */
function speakTurn(speaker, speech) {
  return new Promise((resolve) => {
    if (!isVoiceActive) {
      resolve();
      return;
    }
    
    // Cancel any current speech
    window.speechSynthesis.cancel();
    
    // Clean speech from emojis or markdown bold for better pronunciation
    let cleanSpeech = speech.replace(/[\u2700-\u27BF]|[\uE000-\uF8FF]|\uD83C[\uDC00-\uDFFF]|\uD83D[\uDC00-\uDFFF]|[\u2011-\u26FF]|\uD83E[\uDD00-\uDFFF]/g, '');
    cleanSpeech = cleanSpeech.replace(/\*\*|__/g, '');
    
    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    
    // Allocate voice metrics based on agent characteristics
    let pitch = 1.0;
    let rate = 1.0;
    
    const lowerSpeaker = speaker.toLowerCase();
    
    if (lowerSpeaker.includes("moderator")) {
      pitch = 0.95;
      rate = 0.95;
    } else if (lowerSpeaker.includes("loyalist") || lowerSpeaker.includes("fanboy")) {
      pitch = 1.15;
      rate = 1.15;
    } else if (lowerSpeaker.includes("skeptic") || lowerSpeaker.includes("critic")) {
      pitch = 0.85;
      rate = 0.95;
    } else if (lowerSpeaker.includes("short-seller") || lowerSpeaker.includes("short seller")) {
      pitch = 0.8;
      rate = 1.15;
    } else if (lowerSpeaker.includes("panic") || lowerSpeaker.includes("retail")) {
      pitch = 1.25;
      rate = 1.25;
    } else if (lowerSpeaker.includes("value investor") || lowerSpeaker.includes("dividend")) {
      pitch = 0.9;
      rate = 0.85;
    } else if (lowerSpeaker.includes("day trader") || lowerSpeaker.includes("quantitative")) {
      pitch = 1.0;
      rate = 1.30;
    } else if (lowerSpeaker.includes("watchdog") || lowerSpeaker.includes("regulatory")) {
      pitch = 0.75;
      rate = 0.80;
    } else if (lowerSpeaker.includes("economist")) {
      pitch = 1.02;
      rate = 0.90;
    } else if (lowerSpeaker.includes("insider") || lowerSpeaker.includes("employee")) {
      pitch = 1.05;
      rate = 1.0;
    } else if (lowerSpeaker.includes("expert")) {
      pitch = 0.98;
      rate = 1.05;
    }
    
    utterance.pitch = pitch;
    utterance.rate = rate;
    
    // Assign a distinct voice by hashing speaker name to pick from available voices
    const voices = window.speechSynthesis.getVoices().filter(v => v.lang.startsWith('en'));
    if (voices.length > 0) {
      let hash = 0;
      for (let i = 0; i < speaker.length; i++) {
        hash = speaker.charCodeAt(i) + ((hash << 5) - hash);
      }
      const voiceIndex = Math.abs(hash) % voices.length;
      utterance.voice = voices[voiceIndex];
    }
    
    // Handle end/error states to resolve promise
    utterance.onend = () => {
      resolve();
    };
    
    utterance.onerror = (e) => {
      console.warn("TTS speak error:", e);
      resolve();
    };
    
    window.speechSynthesis.speak(utterance);
    
    // Fallback safety timeout
    setTimeout(() => {
      resolve();
    }, 15000); 
  });
}

// Pre-warm Speech Synthesis voices list immediately to ensure it's loaded before the first turn
if (typeof window !== 'undefined' && window.speechSynthesis) {
  window.speechSynthesis.getVoices();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = () => {
      window.speechSynthesis.getVoices();
    };
  }
}
