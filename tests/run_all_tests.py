"""
Master Test Runner: Executes all Phase test suites sequentially
"""
import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PYTHON_EXE = BASE_DIR / "venv" / "Scripts" / "python.exe"

TESTS = [
    ("Phase 1: Environment & Dependencies", "tests/test_env.py"),
    ("Phase 2: Audio Engine Streaming", "tests/test_audio.py"),
    ("Phase 3: Wake-Word Engine", "tests/test_wakeword.py"),
    ("Phase 4: Wake-Word Evaluation Suite", "tests/eval_wakeword.py"),
    ("Phase 5: Speech-To-Text (faster-whisper)", "tests/test_stt.py"),
    ("Phase 6: Deterministic Command Parser", "tests/test_parser.py"),
    ("Phase 7: Localhost WebSocket Service", "tests/test_service.py"),
    ("Phase 8: Chrome Extension Parity", "tests/test_extension.py"),
    ("Phase 9: End-to-End Hands-Free State Machine", "tests/test_end_to_end.py"),
]

def run_all():
    print("=" * 70)
    print("HEY YOUTUBE — COMPLETE SYSTEM VERIFICATION RUNNER")
    print("=" * 70)

    passed_count = 0
    failed_count = 0

    for name, script in TESTS:
        script_path = BASE_DIR / script
        print(f"\n>>> Running {name} ({script})...")
        res = subprocess.run([str(PYTHON_EXE), str(script_path)], capture_output=False)
        if res.returncode == 0:
            passed_count += 1
            print(f">>> [PASS] {name}")
        else:
            failed_count += 1
            print(f">>> [FAIL] {name} (Exit code: {res.returncode})")

    print("\n" + "=" * 70)
    print(f"FINAL SUMMARY: {passed_count} Passed, {failed_count} Failed out of {len(TESTS)} test suites.")
    print("=" * 70)

    if failed_count == 0:
        print("ALL TESTS PASSED! SYSTEM IS 100% PRODUCTION READY.")
    else:
        sys.exit(1)

if __name__ == "__main__":
    run_all()
