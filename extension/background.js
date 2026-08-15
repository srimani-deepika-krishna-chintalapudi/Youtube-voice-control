/**
 * Background Service Worker (Manifest V3)
 * Maintains persistent WebSocket connection to local Python engine (ws://127.0.0.1:8765)
 * and relays messages to active YouTube tabs.
 */

const WS_URL = "ws://127.0.0.1:8765";
let socket = null;
let reconnectTimer = null;

function connectWebSocket() {
  if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
    return;
  }

  try {
    socket = new WebSocket(WS_URL);

    socket.onopen = () => {
      console.log("[HeyYouTube Background] Connected to local Python service.");
      broadcastToTabs({ type: "STATUS", status: "CONNECTED" });
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    socket.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        console.log("[HeyYouTube Background] Received:", message);
        broadcastToTabs(message);
      } catch (err) {
        console.error("[HeyYouTube Background] Error parsing message:", err);
      }
    };

    socket.onclose = () => {
      console.log("[HeyYouTube Background] Disconnected from Python service. Reconnecting in 3s...");
      broadcastToTabs({ type: "STATUS", status: "DISCONNECTED" });
      scheduleReconnect();
    };

    socket.onerror = (err) => {
      console.warn("[HeyYouTube Background] WebSocket error:", err);
      socket.close();
    };
  } catch (err) {
    console.error("[HeyYouTube Background] Connection error:", err);
    scheduleReconnect();
  }
}

function scheduleReconnect() {
  if (!reconnectTimer) {
    reconnectTimer = setTimeout(() => {
      reconnectTimer = null;
      connectWebSocket();
    }, 3000);
  }
}

function broadcastToTabs(message) {
  chrome.tabs.query({ url: "*://www.youtube.com/*" }, (tabs) => {
    if (!tabs || tabs.length === 0) return;
    for (const tab of tabs) {
      if (tab.id) {
        chrome.tabs.sendMessage(tab.id, message).catch(() => {
          // Tab might not be ready or injected yet
        });
      }
    }
  });
}

// Listen for messages from content scripts (e.g. user toggling pause in UI)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(request));
    sendResponse({ status: "SENT" });
  } else {
    sendResponse({ status: "NOT_CONNECTED" });
  }
  return true;
});

// Start connection on worker activation
connectWebSocket();

// Periodic heartbeat to keep connection alive
setInterval(() => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify({ type: "PING" }));
  } else {
    connectWebSocket();
  }
}, 10000);
