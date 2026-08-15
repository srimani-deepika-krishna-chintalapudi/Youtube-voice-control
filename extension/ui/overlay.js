/**
 * Hey YouTube - Unobtrusive Floating Status UI Controller
 */

class VoiceStatusOverlay {
  constructor() {
    this.root = null;
    this.container = null;
    this.dot = null;
    this.textLabel = null;
    this.toggleBtn = null;
    this.isPaused = false;
    this.revertTimeout = null;
    this.init();
  }

  init() {
    if (document.getElementById("hey-youtube-overlay-root")) return;

    this.root = document.createElement("div");
    this.root.id = "hey-youtube-overlay-root";

    this.container = document.createElement("div");
    this.container.className = "hy-pill-container hy-status-waiting";

    this.dot = document.createElement("div");
    this.dot.className = "hy-status-dot";

    this.textLabel = document.createElement("span");
    this.textLabel.className = "hy-status-text";
    this.textLabel.textContent = "Waiting for 'Hey YouTube'";

    this.toggleBtn = document.createElement("button");
    this.toggleBtn.className = "hy-toggle-btn";
    this.toggleBtn.title = "Pause/Resume Voice Listening";
    this.toggleBtn.innerHTML = "⏸️";
    this.toggleBtn.onclick = (e) => {
      e.stopPropagation();
      this.togglePause();
    };

    this.container.appendChild(this.dot);
    this.container.appendChild(this.textLabel);
    this.container.appendChild(this.toggleBtn);
    this.root.appendChild(this.container);

    document.body.appendChild(this.root);
  }

  setStatus(state, customMessage = null) {
    if (this.revertTimeout) {
      clearTimeout(this.revertTimeout);
      this.revertTimeout = null;
    }

    this.container.className = "hy-pill-container";

    switch (state) {
      case "WAITING":
      case "WAITING_FOR_WAKE_WORD":
        this.container.classList.add("hy-status-waiting");
        this.textLabel.textContent = customMessage || "Waiting for 'Hey YouTube'";
        this.toggleBtn.innerHTML = "⏸️";
        break;

      case "LISTENING":
      case "LISTENING_FOR_COMMAND":
        this.container.classList.add("hy-status-listening");
        this.textLabel.textContent = customMessage || "Listening for command...";
        break;

      case "PROCESSING":
      case "PROCESSING_COMMAND":
        this.container.classList.add("hy-status-processing");
        this.textLabel.textContent = customMessage || "Processing command...";
        break;

      case "EXECUTED":
        this.container.classList.add("hy-status-executed");
        this.textLabel.innerHTML = customMessage || "⚡ Command Executed";
        // Auto-revert back to waiting state after 2.5s
        this.revertTimeout = setTimeout(() => {
          this.setStatus("WAITING");
        }, 2500);
        break;

      case "PAUSED":
        this.container.classList.add("hy-status-paused");
        this.textLabel.textContent = "Listening Paused";
        this.toggleBtn.innerHTML = "▶️";
        break;

      case "DISCONNECTED":
        this.container.classList.add("hy-status-disconnected");
        this.textLabel.textContent = "Service Offline (Run Python Engine)";
        break;

      default:
        this.container.classList.add("hy-status-waiting");
        this.textLabel.textContent = customMessage || state;
    }
  }

  togglePause() {
    this.isPaused = !this.isPaused;
    chrome.runtime.sendMessage({
      type: "TOGGLE_LISTENING",
      paused: this.isPaused,
    });
    if (this.isPaused) {
      this.setStatus("PAUSED");
    } else {
      this.setStatus("WAITING");
    }
  }
}

// Make globally available to content script
window.HeyYouTubeOverlay = VoiceStatusOverlay;
