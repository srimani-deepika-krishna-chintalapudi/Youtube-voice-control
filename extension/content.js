/**
 * Hey YouTube — YouTube Video Controller Content Script
 * Directly controls HTML5 video playback and renders unobtrusive feedback overlay.
 */

let overlay = null;

function getYouTubeVideo() {
  return (
    document.querySelector("video.html5-main-video") ||
    document.querySelector("video")
  );
}

function initExtension() {
  if (!overlay && window.HeyYouTubeOverlay) {
    overlay = new window.HeyYouTubeOverlay();
  }
}

// Ensure overlay exists on YouTube dynamic page loads
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initExtension);
} else {
  initExtension();
}

window.addEventListener("yt-navigate-finish", () => {
  initExtension();
});

// Handle incoming commands and state updates from background.js
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  initExtension();
  if (!message || !message.type) return;

  if (message.type === "STATUS") {
    if (message.status === "CONNECTED") {
      overlay.setStatus("WAITING");
    } else {
      overlay.setStatus("DISCONNECTED");
    }
  } else if (message.type === "STATE_CHANGE") {
    overlay.setStatus(message.state, message.detail);
  } else if (message.type === "COMMAND") {
    executeVideoCommand(message);
  }

  sendResponse({ status: "HANDLED" });
  return true;
});

function executeVideoCommand(cmd) {
  const video = getYouTubeVideo();
  if (!video) {
    console.warn("[HeyYouTube] No active YouTube video element found.");
    overlay.setStatus("EXECUTED", "⚠️ No Video Found");
    return;
  }

  const intent = cmd.intent;
  const val = cmd.value;
  let feedbackText = `⚡ ${intent}`;

  switch (intent) {
    case "PLAY":
      video.play();
      feedbackText = "⚡ Playing";
      break;

    case "PAUSE":
      video.pause();
      feedbackText = "⚡ Paused";
      break;

    case "TOGGLE_PLAYBACK":
      if (video.paused) {
        video.play();
        feedbackText = "⚡ Playing";
      } else {
        video.pause();
        feedbackText = "⚡ Paused";
      }
      break;

    case "REWIND": {
      const sec = val || 10;
      video.currentTime = Math.max(0, video.currentTime - sec);
      feedbackText = `⚡ Rewound ${sec}s`;
      break;
    }

    case "FORWARD": {
      const sec = val || 10;
      video.currentTime = Math.min(video.duration || Infinity, video.currentTime + sec);
      feedbackText = `⚡ Forward ${sec}s`;
      break;
    }

    case "RESTART":
      video.currentTime = 0;
      video.play();
      feedbackText = "⚡ Restarted";
      break;

    case "SPEED_UP": {
      const step = val || 0.25;
      const newRate = Math.min(2.0, Number((video.playbackRate + step).toFixed(2)));
      video.playbackRate = newRate;
      feedbackText = `⚡ Speed: ${newRate}x`;
      break;
    }

    case "SPEED_DOWN": {
      const step = val || 0.25;
      const newRate = Math.max(0.25, Number((video.playbackRate - step).toFixed(2)));
      video.playbackRate = newRate;
      feedbackText = `⚡ Speed: ${newRate}x`;
      break;
    }

    case "SET_SPEED": {
      const rate = val || 1.0;
      video.playbackRate = rate;
      feedbackText = `⚡ Speed: ${rate}x`;
      break;
    }

    case "MUTE":
      video.muted = true;
      feedbackText = "⚡ Muted";
      break;

    case "UNMUTE":
      video.muted = false;
      feedbackText = "⚡ Unmuted";
      break;

    case "VOLUME_UP": {
      const step = val || 0.1;
      video.volume = Math.min(1.0, Number((video.volume + step).toFixed(2)));
      video.muted = false;
      feedbackText = `⚡ Volume: ${Math.round(video.volume * 100)}%`;
      break;
    }

    case "VOLUME_DOWN": {
      const step = val || 0.1;
      video.volume = Math.max(0.0, Number((video.volume - step).toFixed(2)));
      feedbackText = `⚡ Volume: ${Math.round(video.volume * 100)}%`;
      break;
    }

    case "FULLSCREEN": {
      const fsBtn = document.querySelector(".ytp-fullscreen-button");
      if (fsBtn) {
        fsBtn.click();
      } else {
        video.requestFullscreen?.();
      }
      feedbackText = "⚡ Fullscreen";
      break;
    }

    case "EXIT_FULLSCREEN": {
      if (document.fullscreenElement) {
        document.exitFullscreen();
      }
      feedbackText = "⚡ Normal Screen";
      break;
    }

    case "NEXT": {
      const nextBtn = document.querySelector(".ytp-next-button");
      if (nextBtn) {
        nextBtn.click();
        feedbackText = "⚡ Next Video";
      }
      break;
    }

    case "PREVIOUS": {
      const prevBtn = document.querySelector(".ytp-prev-button");
      if (prevBtn) {
        prevBtn.click();
        feedbackText = "⚡ Previous Video";
      } else {
        window.history.back();
        feedbackText = "⚡ Previous Video";
      }
      break;
    }

    default:
      feedbackText = `⚡ ${intent}`;
  }

  overlay.setStatus("EXECUTED", feedbackText);
}
