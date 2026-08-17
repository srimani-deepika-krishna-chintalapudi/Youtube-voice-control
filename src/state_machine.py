"""
Hey YouTube - End-to-End Hands-Free State Machine
Coordinates Audio Recording, Wake Word, Speech-To-Text, Parser, and WebSocket Service.
"""
import time
import logging
import threading
from enum import Enum
from typing import Optional

from src.config import (
    COMMAND_RECORD_SECONDS,
    WAKE_WORD_THRESHOLD,
)
from src.audio.recorder import AudioRecorder
from src.wakeword.engine import WakeWordEngine
from src.stt.transcriber import LocalTranscriber
from src.parser.command_parser import parse_command, CommandIntent
from src.service.server import LocalCommandService

logger = logging.getLogger(__name__)


class ControllerState(Enum):
    WAITING_FOR_WAKE_WORD = "WAITING_FOR_WAKE_WORD"
    WAKE_WORD_DETECTED = "WAKE_WORD_DETECTED"
    LISTENING_FOR_COMMAND = "LISTENING_FOR_COMMAND"
    PROCESSING_COMMAND = "PROCESSING_COMMAND"
    EXECUTE_COMMAND = "EXECUTE_COMMAND"
    RETURN_TO_WAKE_WORD_LISTENING = "RETURN_TO_WAKE_WORD_LISTENING"


class VoiceControllerStateMachine:
    """
    Orchestrates the 6-state hands-free voice control pipeline.
    """

    def __init__(
        self,
        recorder: Optional[AudioRecorder] = None,
        wake_engine: Optional[WakeWordEngine] = None,
        transcriber: Optional[LocalTranscriber] = None,
        service: Optional[LocalCommandService] = None,
    ):
        self.recorder = recorder or AudioRecorder()
        self.wake_engine = wake_engine or WakeWordEngine()
        self.transcriber = transcriber or LocalTranscriber()
        self.service = service or LocalCommandService()

        self.current_state = ControllerState.WAITING_FOR_WAKE_WORD
        self._running = False
        self._worker_thread: Optional[threading.Thread] = None

    def _set_state(self, new_state: ControllerState, detail: Optional[str] = None):
        """Updates internal state and informs connected browser extension."""
        self.current_state = new_state
        logger.info(f"State -> {new_state.value} {f'({detail})' if detail else ''}")
        self.service.send_state(new_state.value, detail)

    def _run_loop(self):
        """Main hands-free processing loop."""
        logger.info("Voice Controller State Machine started.")
        self.recorder.start()
        self._set_state(ControllerState.WAITING_FOR_WAKE_WORD)
        print("\n" + "=" * 60)
        print("[ACTIVE] WAITING FOR 'HEY YOUTUBE'...")
        print("=" * 60)

        while self._running:
            try:
                # If user paused listening from extension UI, idle briefly
                if self.service.paused_by_user:
                    time.sleep(0.2)
                    continue

                # ========================================================
                # STATE 1: WAITING_FOR_WAKE_WORD
                # ========================================================
                chunk = self.recorder.get_chunk(timeout=0.2)
                if chunk is None:
                    continue

                detected, score = self.wake_engine.is_wake_word_detected(chunk)
                if not detected:
                    continue

                # ========================================================
                # STATE 2: WAKE_WORD_DETECTED
                # ========================================================
                print("\n" + "*" * 50)
                print(">>> WAKE WORD DETECTED: 'Hey YouTube'!")
                print(">>> Listening for command now...")
                print("*" * 50)

                self._set_state(ControllerState.WAKE_WORD_DETECTED, f"Score: {score:.2f}")

                # ========================================================
                # STATE 3: LISTENING_FOR_COMMAND
                # ========================================================
                self._set_state(ControllerState.LISTENING_FOR_COMMAND)
                audio_command = self.recorder.record_command(
                    max_duration_sec=5.0,
                    silence_duration_sec=0.9,
                )

                # ========================================================
                # STATE 4: PROCESSING_COMMAND
                # ========================================================
                self._set_state(ControllerState.PROCESSING_COMMAND)
                transcript = self.transcriber.transcribe(audio_command)
                print(f"[TRANSCRIPT] HEARD: '{transcript}'")

                # ========================================================
                # STATE 5: EXECUTE_COMMAND
                # ========================================================
                if transcript:
                    parsed = parse_command(transcript)
                    intent = parsed.get("intent")
                    val = parsed.get("value")
                    raw = parsed.get("raw")

                    if intent != CommandIntent.UNKNOWN:
                        val_str = f"({val}s)" if val is not None else ""
                        print(f"[ACTION] EXECUTING: {intent} {val_str}")
                        self._set_state(ControllerState.EXECUTE_COMMAND, f"{intent} {val or ''}".strip())
                        self.service.send_command(intent=intent, value=val, raw_text=raw)
                    else:
                        print(f"[WARNING] UNRECOGNIZED COMMAND: '{transcript}'")
                        self.service.send_state("EXECUTED", "Unrecognized Command")
                else:
                    print("[INFO] No command speech detected in window.")
                    self.service.send_state("WAITING_FOR_WAKE_WORD")

                # ========================================================
                # STATE 6: RETURN_TO_WAKE_WORD_LISTENING
                # ========================================================
                self._set_state(ControllerState.RETURN_TO_WAKE_WORD_LISTENING)
                self.wake_engine.reset()
                time.sleep(0.5)
                self._set_state(ControllerState.WAITING_FOR_WAKE_WORD)
                print("\n[ACTIVE] WAITING FOR 'HEY YOUTUBE'...")

            except Exception as e:
                logger.error(f"Error in state machine loop: {e}", exc_info=True)
                time.sleep(0.5)

        self.recorder.stop()
        logger.info("Voice Controller State Machine stopped.")

    def start(self):
        """Starts background WebSocket service and state machine loop."""
        if self._running:
            return

        self._running = True
        self.service.start()
        self._worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self._worker_thread.start()

    def stop(self):
        """Stops the state machine and releases resources."""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=2.0)
        self.service.stop()
