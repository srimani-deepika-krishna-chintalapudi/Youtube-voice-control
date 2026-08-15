"""
Phase 1 Verification: Environment & Dependencies Check
"""
import sys

def check_environment():
    print("=" * 50)
    print("PHASE 1: ENVIRONMENT & HARDWARE VERIFICATION")
    print("=" * 50)
    print(f"Python Version: {sys.version}")

    # 1. Check sounddevice & audio devices
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        print("\n[OK] sounddevice imported successfully.")
        print(f"Detected {len(devices)} audio device(s):")
        for idx, dev in enumerate(devices):
            if dev.get('max_input_channels', 0) > 0:
                print(f"  - Input Device [{idx}]: {dev['name']} (Channels: {dev['max_input_channels']}, SampleRate: {dev['default_samplerate']})")
    except Exception as e:
        print(f"\n[FAIL] sounddevice error: {e}")

    # 2. Check openwakeword & onnxruntime
    try:
        import onnxruntime as ort
        print(f"\n[OK] onnxruntime version {ort.__version__} loaded.")
        from openwakeword.model import Model
        print("[OK] openwakeword imported successfully.")
    except Exception as e:
        print(f"\n[FAIL] openwakeword/onnxruntime error: {e}")

    # 3. Check faster-whisper
    try:
        from faster_whisper import WhisperModel
        print("\n[OK] faster-whisper imported successfully.")
    except Exception as e:
        print(f"\n[FAIL] faster-whisper error: {e}")

    # 4. Check numpy & scipy
    try:
        import numpy as np
        import scipy
        print(f"\n[OK] numpy version: {np.__version__}, scipy version: {scipy.__version__}")
    except Exception as e:
        print(f"\n[FAIL] numpy/scipy error: {e}")

    print("\n" + "=" * 50)
    print("PHASE 1 ENVIRONMENT VERIFICATION COMPLETE")
    print("=" * 50)

if __name__ == "__main__":
    check_environment()
