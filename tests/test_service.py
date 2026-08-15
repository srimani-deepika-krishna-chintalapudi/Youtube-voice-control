"""
Phase 7 Test: Localhost WebSocket Service Verification
Tests WebSocket server binding, client connection, ping-pong, and thread-safe command broadcasting.
"""
import sys
import time
import json
import asyncio
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.service.server import LocalCommandService
from src.config import SERVER_HOST, SERVER_PORT
import websockets

async def simulate_browser_client(messages_received: list):
    """Simulates a Chrome extension connecting to the Python service."""
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    async with websockets.connect(uri) as ws:
        # 1. Receive initial status message
        init_msg = await ws.recv()
        messages_received.append(json.loads(init_msg))

        # 2. Send PING
        await ws.send(json.dumps({"type": "PING"}))
        pong = await ws.recv()
        messages_received.append(json.loads(pong))

        # 3. Wait for broadcast messages from test runner
        for _ in range(2):
            broadcast = await ws.recv()
            messages_received.append(json.loads(broadcast))

def test_service():
    print("=" * 60)
    print("PHASE 7 TEST: LOCALHOST WEBSOCKET COMMUNICATION SERVICE")
    print("=" * 60)

    # 1. Start Server
    print(f"\n[Step 1] Starting WebSocket service on ws://{SERVER_HOST}:{SERVER_PORT}...")
    service = LocalCommandService()
    service.start()
    time.sleep(0.5)
    assert service.is_running, "Service failed to start!"
    print("[OK] Service is active.")

    # 2. Run Simulated Client
    print("\n[Step 2] Connecting simulated Chrome Extension client...")
    received = []

    def trigger_broadcasts():
        time.sleep(0.3)
        # Broadcast state transition
        service.send_state("LISTENING_FOR_COMMAND")
        time.sleep(0.1)
        # Broadcast command
        service.send_command("REWIND", 20, "go back 20 seconds")

    import threading
    t = threading.Thread(target=trigger_broadcasts)
    t.start()

    # Run asyncio client loop
    asyncio.run(simulate_browser_client(received))
    t.join()

    print(f"[OK] Client received {len(received)} message(s):")
    for idx, msg in enumerate(received):
        print(f"  [{idx+1}] {msg}")

    # Assertions
    assert received[0].get("type") == "STATUS" and received[0].get("status") == "CONNECTED"
    assert received[1].get("type") == "PONG"
    assert received[2].get("type") == "STATE_CHANGE" and received[2].get("state") == "LISTENING_FOR_COMMAND"
    assert received[3].get("type") == "COMMAND" and received[3].get("intent") == "REWIND" and received[3].get("value") == 20

    print("\n[Step 3] Stopping WebSocket service...")
    service.stop()
    print("[OK] Service stopped cleanly.")

    print("\n" + "=" * 60)
    print("PHASE 7 SERVICE VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_service()
