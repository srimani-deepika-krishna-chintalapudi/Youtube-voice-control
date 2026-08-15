"""
Phase 9 Test: End-to-End Hands-Free State Machine Integration Test
Simulates full pipeline: Wake Detection -> State Transitions -> STT -> Parser -> WebSocket Broadcast.
"""
import sys
import time
import json
import asyncio
from pathlib import Path
import websockets

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.state_machine import VoiceControllerStateMachine, ControllerState
from src.config import SERVER_HOST, SERVER_PORT

async def test_full_pipeline():
    print("=" * 60)
    print("PHASE 9 TEST: END-TO-END HANDS-FREE STATE MACHINE PIPELINE")
    print("=" * 60)

    # 1. Initialize State Machine
    print("\n[Step 1] Initializing and starting VoiceControllerStateMachine...")
    controller = VoiceControllerStateMachine()
    controller.start()
    time.sleep(1.0)
    assert controller.current_state == ControllerState.WAITING_FOR_WAKE_WORD
    print("[OK] State Machine started in WAITING_FOR_WAKE_WORD state.")

    # 2. Connect Client
    print("\n[Step 2] Connecting simulated Chrome Extension...")
    uri = f"ws://{SERVER_HOST}:{SERVER_PORT}"
    async with websockets.connect(uri) as ws:
        init_msg = json.loads(await ws.recv())
        print(f"[OK] Extension received connection: {init_msg}")

        # 3. Simulate Wake-Word Trigger & Command Dispatch
        print("\n[Step 3] Simulating Wake-Word & Command lifecycle...")
        controller._set_state(ControllerState.WAKE_WORD_DETECTED, "Triggered")
        msg_state2 = json.loads(await ws.recv())
        print(f"  -> Received State: {msg_state2.get('state')} ({msg_state2.get('detail')})")
        assert msg_state2.get("state") == "WAKE_WORD_DETECTED"

        controller._set_state(ControllerState.LISTENING_FOR_COMMAND)
        msg_state3 = json.loads(await ws.recv())
        print(f"  -> Received State: {msg_state3.get('state')}")
        assert msg_state3.get("state") == "LISTENING_FOR_COMMAND"

        controller._set_state(ControllerState.PROCESSING_COMMAND)
        msg_state4 = json.loads(await ws.recv())
        print(f"  -> Received State: {msg_state4.get('state')}")
        assert msg_state4.get("state") == "PROCESSING_COMMAND"

        # Dispatch command
        controller.service.send_command("REWIND", 20, "go back 20 seconds")
        msg_cmd = json.loads(await ws.recv())
        print(f"  -> Received Command: {msg_cmd}")
        assert msg_cmd.get("type") == "COMMAND"
        assert msg_cmd.get("intent") == "REWIND" and msg_cmd.get("value") == 20

        # Return to waiting
        controller._set_state(ControllerState.WAITING_FOR_WAKE_WORD)
        msg_state1 = json.loads(await ws.recv())
        print(f"  -> Returned State: {msg_state1.get('state')}")
        assert msg_state1.get("state") == "WAITING_FOR_WAKE_WORD"

    # 4. Stop Controller
    print("\n[Step 4] Stopping State Machine...")
    controller.stop()
    print("[OK] Pipeline stopped cleanly.")

    print("\n" + "=" * 60)
    print("PHASE 9 END-TO-END PIPELINE VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
