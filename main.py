"""
Hey YouTube — Privacy-First Hands-Free Video Controller
Main Application Entry Point
"""
import sys
import time
import logging
from pathlib import Path

# Set up project root in path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

from src.config import SERVER_HOST, SERVER_PORT, SAMPLE_RATE, MIC_DEVICE_INDEX
from src.state_machine import VoiceControllerStateMachine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("HeyYouTube")


def print_banner():
    banner = f"""
======================================================================
  HEY YOUTUBE — PRIVACY-FIRST HANDS-FREE VIDEO CONTROLLER
======================================================================
  [Local Voice Engine]
  - Mic Sample Rate:   {SAMPLE_RATE} Hz
  - Device Index:      {MIC_DEVICE_INDEX}
  - Wake Word:         "Hey YouTube" (Local ONNX)
  - STT Engine:        faster-whisper (Local int8 CPU, on-demand only)
  - Parser:            Deterministic rules & entities
  - Chrome Extension:  ws://{SERVER_HOST}:{SERVER_PORT}
======================================================================
  Ready to control YouTube!
  1. Say "Hey YouTube"
  2. Speak your command (e.g. "pause", "go back 20 seconds", "speed up")
  3. Keep crocheting and enjoy!
======================================================================
  Press Ctrl+C to stop the engine.
"""
    print(banner)


def main():
    print_banner()

    controller = VoiceControllerStateMachine()
    controller.start()

    try:
        while True:
            time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping Hey YouTube Voice Controller...")
    finally:
        controller.stop()
        print("Engine stopped cleanly. Goodbye!")


if __name__ == "__main__":
    main()
