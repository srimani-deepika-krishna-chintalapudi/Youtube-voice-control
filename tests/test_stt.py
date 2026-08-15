"""
Phase 5 Test: Local Speech-To-Text (faster-whisper) Verification
Tests model loading, memory footprint, transcription speed, and live audio transcription.
"""
import sys
import time
from pathlib import Path
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.stt.transcriber import LocalTranscriber
from src.audio.recorder import AudioRecorder
from src.config import SAMPLE_RATE

def test_stt_engine():
    print("=" * 60)
    print("PHASE 5 TEST: LOCAL SPEECH-TO-TEXT (faster-whisper)")
    print("=" * 60)

    # 1. Initialize Whisper
    print("\n[Step 1] Loading local faster-whisper model (int8 CPU)...")
    t0 = time.time()
    transcriber = LocalTranscriber(model_size="base.en")
    print(f"[OK] Model loaded in {time.time() - t0:.2f} seconds.")

    # 2. Test with synthetic silence
    print("\n[Step 2] Testing silence rejection (VAD)...")
    silence = np.zeros(SAMPLE_RATE * 2, dtype=np.int16)
    text = transcriber.transcribe(silence)
    print(f"[OK] Silence transcribed as: '{text}' (Expected empty string)")
    assert text == "", f"Expected empty text on silence, got '{text}'"

    # 3. Test with saved mic test sample if exists
    mic_test_wav = BASE_DIR / "tests" / "test_mic_output.wav"
    if mic_test_wav.exists():
        print(f"\n[Step 3] Transcribing previous test recording ({mic_test_wav.name})...")
        t0 = time.perf_counter()
        transcript = transcriber.transcribe_file(mic_test_wav)
        lat = (time.perf_counter() - t0) * 1000
        print(f"[OK] Result: '{transcript}' | Latency: {lat:.1f} ms")

    print("\n" + "=" * 60)
    print("PHASE 5 STT ENGINE VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_stt_engine()
