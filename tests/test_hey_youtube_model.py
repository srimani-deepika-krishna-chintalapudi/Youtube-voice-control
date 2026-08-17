from pathlib import Path
import numpy as np
import sounddevice as sd
from openwakeword.model import Model

MODEL_PATH = Path("models/hey_youtube.onnx")

SAMPLE_RATE = 16000
CHUNK_SIZE = 1280  # 80 ms

print("=" * 50)
print("HEY YOUTUBE — RAW ONNX MODEL TEST")
print("=" * 50)

if not MODEL_PATH.exists():
    print(f"ERROR: Model not found: {MODEL_PATH}")
    raise SystemExit(1)

print(f"Loading: {MODEL_PATH}")

model = Model(
    wakeword_models=[str(MODEL_PATH)],
    inference_framework="onnx",
)

print("Model loaded.")
print()
print("Say: HEY YOUTUBE")
print("Do NOT say anything else.")
print("Press Ctrl+C to stop.")
print()

try:
    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SIZE,
    ) as stream:

        while True:
            audio, _ = stream.read(CHUNK_SIZE)

            audio = audio[:, 0]

            scores = model.predict(audio)

            score = max(scores.values()) if scores else 0.0

            print(
                f"\rRaw model score: {score:.4f}",
                end="",
                flush=True,
            )

except KeyboardInterrupt:
    print("\n\nStopped.")