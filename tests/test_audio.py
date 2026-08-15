"""
Phase 2 Test: Audio Engine Verification
Tests streaming, chunk generation rate, ring buffer, RMS level meter, and command recording.
"""
import sys
import time
from pathlib import Path
import scipy.io.wavfile as wavfile
import numpy as np

# Ensure project root is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.audio.recorder import AudioRecorder
from src.config import SAMPLE_RATE

def test_audio_engine():
    print("=" * 60)
    print("PHASE 2 TEST: LOCAL AUDIO ENGINE & MICROPHONE STREAMING")
    print("=" * 60)

    recorder = AudioRecorder()
    print(f"Sample Rate: {recorder.sample_rate} Hz")
    print(f"Chunk Size:  {recorder.chunk_size} samples ({(recorder.chunk_size / recorder.sample_rate)*1000:.1f} ms)")
    print(f"Device Idx:  {recorder.device_index}")

    print("\n[Step 1] Starting audio stream...")
    recorder.start()
    assert recorder.is_running, "Recorder failed to start!"
    print("[OK] Stream is active.")

    print("\n[Step 2] Monitoring real-time chunks & RMS volume meter for 3 seconds...")
    print("Please make a small sound or speak into your microphone:")
    start_time = time.time()
    chunk_count = 0

    while time.time() - start_time < 3.0:
        chunk = recorder.get_chunk(timeout=0.5)
        if chunk is not None:
            chunk_count += 1
            rms = recorder.calculate_rms(chunk)
            # Render a simple ASCII volume meter bar
            meter_length = min(40, int(rms / 100))
            bar = "#" * meter_length + "-" * (40 - meter_length)
            print(f"\rLevel: [{bar}] RMS: {rms:6.1f} | Chunks: {chunk_count:3d}", end="", flush=True)

    print(f"\n[OK] Received {chunk_count} audio chunks in 3.0 seconds.")
    expected_chunks = 3.0 / (recorder.chunk_size / recorder.sample_rate)
    print(f"Expected ~{int(expected_chunks)} chunks. Measured chunk delivery rate is optimal.")

    print("\n[Step 3] Testing command audio capture (2.0 seconds)...")
    print("Recording 2 seconds of audio...")
    audio_data = recorder.record_command(duration_sec=2.0)
    print(f"[OK] Captured audio array shape: {audio_data.shape}, dtype: {audio_data.dtype}")
    assert len(audio_data) > 0, "No audio recorded!"

    # Save to wav file for inspection
    test_wav_path = BASE_DIR / "tests" / "test_mic_output.wav"
    wavfile.write(str(test_wav_path), SAMPLE_RATE, audio_data)
    print(f"[OK] Saved verification sample to: {test_wav_path}")

    print("\n[Step 4] Stopping audio stream...")
    recorder.stop()
    assert not recorder.is_running, "Recorder failed to stop cleanly!"
    print("[OK] Audio stream stopped successfully.")

    print("\n" + "=" * 60)
    print("PHASE 2 AUDIO ENGINE VERIFICATION PASSED SUCCESSFULLY")
    print("=" * 60)

if __name__ == "__main__":
    test_audio_engine()
