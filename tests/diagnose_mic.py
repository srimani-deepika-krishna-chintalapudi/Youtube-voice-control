"""
Diagnostic Tool: Test live microphone volume levels and audio capture.
"""
import sys
import time
from pathlib import Path
import numpy as np
import scipy.io.wavfile as wavfile

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.audio.recorder import AudioRecorder
from src.stt.transcriber import LocalTranscriber
from src.config import SAMPLE_RATE

def diagnose():
    print("=" * 60)
    print("LIVE MICROPHONE & SPEECH DIAGNOSTIC")
    print("=" * 60)

    recorder = AudioRecorder()
    recorder.start()
    print("\n[1] Microphone started. Please say: 'Hey YouTube, pause the video' now!")
    print("Listening for 4 seconds...")

    chunks = []
    start_time = time.time()
    while time.time() - start_time < 4.0:
        chunk = recorder.get_chunk(timeout=0.2)
        if chunk is not None:
            chunks.append(chunk)
            rms = recorder.calculate_rms(chunk)
            bar = "#" * min(40, int(rms / 100)) + "-" * (40 - min(40, int(rms / 100)))
            print(f"\rVolume: [{bar}] RMS: {rms:6.1f}", end="", flush=True)

    recorder.stop()
    print("\n\n[2] Audio captured.")

    if not chunks:
        print("[ERROR] No audio chunks captured! Check microphone settings.")
        return

    full_audio = np.concatenate(chunks)
    diag_wav = BASE_DIR / "tests" / "diagnostic_voice.wav"
    wavfile.write(str(diag_wav), SAMPLE_RATE, full_audio)
    print(f"[3] Saved recording to: {diag_wav}")
    print(f"    Audio length: {len(full_audio)/SAMPLE_RATE:.2f}s | Max amplitude: {np.max(np.abs(full_audio))}")

    print("\n[4] Transcribing captured audio with local faster-whisper...")
    stt = LocalTranscriber(model_size="base.en")
    transcript = stt.transcribe(full_audio)
    print(f"\n==================================================")
    print(f"TRANSCRIPTION HEARD: '{transcript}'")
    print(f"==================================================")

if __name__ == "__main__":
    diagnose()
