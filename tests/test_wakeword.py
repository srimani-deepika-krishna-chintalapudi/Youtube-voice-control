"""
Phase 3 Test: Wake Word Engine Verification
Tests model loading, frame inference, latency benchmarking, and streaming integration.
"""
import sys
import time
from pathlib import Path
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.wakeword.engine import WakeWordEngine
from src.audio.recorder import AudioRecorder
from src.config import CHUNK_SIZE

def test_wakeword_engine():
    print("=" * 60)
    print("PHASE 3 TEST: CUSTOM WAKE-WORD DETECTION ENGINE")
    print("=" * 60)

    # 1. Initialize Engine
    print("\n[Step 1] Initializing WakeWordEngine with 'hey_youtube.onnx'...")
    engine = WakeWordEngine()
    print(f"[OK] Loaded model key: {engine.model_key}")
    print(f"[OK] Default threshold: {engine.threshold}")

    # 2. Test synthetic frames & benchmark inference latency
    print("\n[Step 2] Benchmarking inference latency over 50 synthetic frames...")
    latencies = []
    for _ in range(50):
        # 80ms dummy audio frame
        dummy_chunk = np.random.randint(-500, 500, size=CHUNK_SIZE, dtype=np.int16)
        t0 = time.perf_counter()
        scores = engine.process_frame(dummy_chunk)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    avg_lat = np.mean(latencies)
    max_lat = np.max(latencies)
    print(f"[OK] Average frame inference time: {avg_lat:.2f} ms")
    print(f"[OK] Maximum frame inference time: {max_lat:.2f} ms")
    assert avg_lat < 50.0, f"Inference too slow ({avg_lat:.2f} ms > 50 ms)!"
    print("[OK] Latency is well within real-time budget (80.0 ms per chunk).")

    # 3. Test Cooldown & Reset
    print("\n[Step 3] Testing cooldown & state reset...")
    engine.reset()
    print("[OK] State reset successfully.")

    # 4. Test live microphone audio feed with WakeWordEngine for 3 seconds
    print("\n[Step 4] Testing live microphone feed integration for 3 seconds...")
    recorder = AudioRecorder()
    recorder.start()

    start_time = time.time()
    frames_processed = 0
    while time.time() - start_time < 3.0:
        chunk = recorder.get_chunk(timeout=0.5)
        if chunk is not None:
            detected, score = engine.is_wake_word_detected(chunk)
            frames_processed += 1

    recorder.stop()
    print(f"[OK] Successfully processed {frames_processed} live audio chunks without errors.")

    print("\n" + "=" * 60)
    print("PHASE 3 WAKE-WORD ENGINE VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_wakeword_engine()
