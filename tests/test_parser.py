"""
Phase 6 Test: Deterministic Command Parser Unit Tests
Tests parsing of natural language transcripts across all video control intents.
"""
import sys
from pathlib import Path

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.parser.command_parser import parse_command, CommandIntent

TEST_CASES = [
    # 1. PLAY / PAUSE
    ("pause", CommandIntent.PAUSE, None),
    ("pause the video", CommandIntent.PAUSE, None),
    ("stop", CommandIntent.PAUSE, None),
    ("freeze", CommandIntent.PAUSE, None),
    ("play", CommandIntent.PLAY, None),
    ("resume", CommandIntent.PLAY, None),
    ("continue", CommandIntent.PLAY, None),
    ("start playing", CommandIntent.PLAY, None),
    ("unpause", CommandIntent.PLAY, None),

    # 2. REWIND / SEEK BACK
    ("go back 20 seconds", CommandIntent.REWIND, 20),
    ("rewind 20 seconds", CommandIntent.REWIND, 20),
    ("take me back 20 seconds", CommandIntent.REWIND, 20),
    ("replay the last 20 seconds", CommandIntent.REWIND, 20),
    ("go back thirty seconds", CommandIntent.REWIND, 30),
    ("rewind 15s", CommandIntent.REWIND, 15),
    ("go back 1 minute", CommandIntent.REWIND, 60),
    ("rewind two minutes", CommandIntent.REWIND, 120),
    ("back ten seconds", CommandIntent.REWIND, 10),

    # 3. FORWARD / SKIP AHEAD
    ("forward 10 seconds", CommandIntent.FORWARD, 10),
    ("go forward 30 seconds", CommandIntent.FORWARD, 30),
    ("skip ahead 30 seconds", CommandIntent.FORWARD, 30),
    ("fast forward 15s", CommandIntent.FORWARD, 15),
    ("skip ahead a minute", CommandIntent.FORWARD, 60),

    # 4. RESTART / REPLAY
    ("restart", CommandIntent.RESTART, None),
    ("replay that", CommandIntent.RESTART, None),
    ("start over", CommandIntent.RESTART, None),
    ("from the beginning", CommandIntent.RESTART, None),

    # 5. SPEED CONTROL
    ("slow down", CommandIntent.SPEED_DOWN, 0.25),
    ("speed down", CommandIntent.SPEED_DOWN, 0.25),
    ("make it slower", CommandIntent.SPEED_DOWN, 0.25),
    ("speed up", CommandIntent.SPEED_UP, 0.25),
    ("faster", CommandIntent.SPEED_UP, 0.25),
    ("set speed to 1.5", CommandIntent.SET_SPEED, 1.5),
    ("set speed to 2x", CommandIntent.SET_SPEED, 2.0),
    ("set speed to normal", CommandIntent.SET_SPEED, 1.0),

    # 6. AUDIO & VOLUME
    ("mute", CommandIntent.MUTE, None),
    ("silence", CommandIntent.MUTE, None),
    ("be quiet", CommandIntent.MUTE, None),
    ("unmute", CommandIntent.UNMUTE, None),
    ("sound on", CommandIntent.UNMUTE, None),
    ("volume up", CommandIntent.VOLUME_UP, 0.1),
    ("louder", CommandIntent.VOLUME_UP, 0.1),
    ("volume down", CommandIntent.VOLUME_DOWN, 0.1),
    ("quieter", CommandIntent.VOLUME_DOWN, 0.1),

    # 7. FULLSCREEN
    ("make it full screen", CommandIntent.FULLSCREEN, None),
    ("fullscreen", CommandIntent.FULLSCREEN, None),
    ("maximize", CommandIntent.FULLSCREEN, None),
    ("exit full screen", CommandIntent.EXIT_FULLSCREEN, None),
    ("leave fullscreen", CommandIntent.EXIT_FULLSCREEN, None),

    # 8. PLAYLIST / NAVIGATION
    ("next video", CommandIntent.NEXT, None),
    ("next", CommandIntent.NEXT, None),
    ("previous video", CommandIntent.PREVIOUS, None),
    ("previous", CommandIntent.PREVIOUS, None),

    # 9. WITH WAKE WORD PREFIXES IN STT
    ("hey youtube pause", CommandIntent.PAUSE, None),
    ("hey youtube go back 20 seconds", CommandIntent.REWIND, 20),
]

def run_parser_tests():
    print("=" * 60)
    print("PHASE 6 TEST: DETERMINISTIC COMMAND PARSER")
    print("=" * 60)

    passed = 0
    failed = 0

    for phrase, expected_intent, expected_val in TEST_CASES:
        res = parse_command(phrase)
        actual_intent = res.get("intent")
        actual_val = res.get("value")

        intent_match = (actual_intent == expected_intent)
        val_match = (expected_val is None or actual_val == expected_val)

        if intent_match and val_match:
            passed += 1
            print(f"[PASS] '{phrase}' -> Intent: {actual_intent}, Value: {actual_val}")
        else:
            failed += 1
            print(f"[FAIL] '{phrase}'")
            print(f"       Expected: Intent={expected_intent}, Value={expected_val}")
            print(f"       Actual:   Intent={actual_intent}, Value={actual_val}")

    print("-" * 60)
    print(f"Total: {len(TEST_CASES)} | Passed: {passed} | Failed: {failed}")
    assert failed == 0, f"{failed} test case(s) failed!"
    print("\n" + "=" * 60)
    print("PHASE 6 COMMAND PARSER VERIFICATION PASSED (100% ACCURACY)")
    print("=" * 60)

if __name__ == "__main__":
    run_parser_tests()
