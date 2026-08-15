"""
Localhost WebSocket Service
Secure localhost-only bridge between Python engine and Chrome Extension.
"""
import json
import asyncio
import logging
import threading
from typing import Set, Dict, Any, Optional
import websockets
from websockets.server import WebSocketServerProtocol

from src.config import SERVER_HOST, SERVER_PORT

logger = logging.getLogger(__name__)


class LocalCommandService:
    """
    Manages a background WebSocket server bound strictly to localhost (127.0.0.1).
    Broadcasts voice control intents and state updates to connected Chrome extensions.
    """

    def __init__(self, host: str = SERVER_HOST, port: int = SERVER_PORT):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.server_thread: Optional[threading.Thread] = None
        self.server = None
        self._is_running = False
        self.paused_by_user = False

    async def _register(self, websocket: WebSocketServerProtocol):
        """Registers a new Chrome extension connection."""
        self.clients.add(websocket)
        logger.info(f"Extension connected. Active connections: {len(self.clients)}")
        # Send initial connection confirmation
        await websocket.send(
            json.dumps({"type": "STATUS", "status": "CONNECTED", "paused": self.paused_by_user})
        )

    async def _unregister(self, websocket: WebSocketServerProtocol):
        """Unregisters a disconnected Chrome extension."""
        if websocket in self.clients:
            self.clients.remove(websocket)
            logger.info(f"Extension disconnected. Active connections: {len(self.clients)}")

    async def _handler(self, websocket: WebSocketServerProtocol):
        """Handles incoming messages from the Chrome extension."""
        await self._register(websocket)
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type")
                    if msg_type == "PING":
                        await websocket.send(json.dumps({"type": "PONG"}))
                    elif msg_type == "TOGGLE_LISTENING":
                        self.paused_by_user = data.get("paused", not self.paused_by_user)
                        logger.info(f"Listening state toggled by user: paused={self.paused_by_user}")
                        self.broadcast_sync({"type": "LISTENING_STATE", "paused": self.paused_by_user})
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self._unregister(websocket)

    def _run_server(self):
        """Internal worker function running inside a dedicated background thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        async def serve():
            # Start WebSocket server bound to 127.0.0.1
            self.server = await websockets.serve(self._handler, self.host, self.port)
            logger.info(f"Local WebSocket service running at ws://{self.host}:{self.port}")
            self._is_running = True
            await self.server.wait_closed()

        try:
            self.loop.run_until_complete(serve())
        except Exception as e:
            logger.error(f"WebSocket service error: {e}")
        finally:
            self._is_running = False

    def start(self):
        """Starts the WebSocket server in a background daemon thread."""
        if self._is_running:
            return

        self.server_thread = threading.Thread(target=self._run_server, daemon=True)
        self.server_thread.start()

    def stop(self):
        """Stops the WebSocket server cleanly."""
        if self.loop and self.server:
            try:
                self.loop.call_soon_threadsafe(self.server.close)
                self.loop.call_soon_threadsafe(self.loop.stop)
            except Exception:
                pass
        self._is_running = False
        if self.server_thread and self.server_thread.is_alive():
            self.server_thread.join(timeout=1.0)

    def broadcast_sync(self, payload: Dict[str, Any]):
        """
        Thread-safe broadcast helper to send messages from any thread to all connected browser tabs.
        """
        if not self.loop or not self.clients:
            return

        message = json.dumps(payload)

        async def _send_all():
            if self.clients:
                # Send to all connected clients in parallel
                await asyncio.gather(
                    *[client.send(message) for client in list(self.clients)],
                    return_exceptions=True,
                )

        asyncio.run_coroutine_threadsafe(_send_all(), self.loop)

    def send_command(self, intent: str, value: Any = None, raw_text: str = ""):
        """Helper to broadcast a structured command."""
        self.broadcast_sync({
            "type": "COMMAND",
            "intent": intent,
            "value": value,
            "raw": raw_text,
        })

    def send_state(self, state: str, detail: Optional[str] = None):
        """Helper to broadcast a state transition."""
        self.broadcast_sync({
            "type": "STATE_CHANGE",
            "state": state,
            "detail": detail,
        })

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def client_count(self) -> int:
        return len(self.clients)
