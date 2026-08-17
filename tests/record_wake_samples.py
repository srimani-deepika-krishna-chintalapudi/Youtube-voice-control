import os
import time
import wave

import numpy as np
import sounddevice as sd

SAMPLE_RATE = 16000
CHANNELS = 1
DURATION = 2.0

OUTPUT_DIR = "models/training_data/positive_human"
NUM_SAMPLES = 30

os.makedirs(OUTPUT_DIR, exist_ok=True)

print("=" * 55)
print("HEY YOUTUBE - HUMAN POSITIVE DATASET RECORDER")
print("=" * 55)
print()
print("You will record 30 different examples.")
print()
print('Say ONLY: "Hey YouTube"')
print()
print("Vary naturally:")
print("- normal voice")
print("- slightly louder")
print("- slightly quieter")
print("- faster")
print("- slower")
print("- closer to microphone")
print("- farther from microphone")
print()
print("The recordings are saved locally.")
print()

input("Press ENTER to begin...")

for i in range(NUM_SAMPLES):
    print()
    print(f"Recording {i + 1}/{NUM_SAMPLES}")
    print("Get ready...")

    for n in [3, 2, 1]:
        print(n)
        time.sleep(1)

    print("🎤 SAY: Hey YouTube")

    audio = sd.rec(
        int(DURATION * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=CHANNELS,
        dtype="int16",
    )

    sd.wait()

    filename = os.path.join(
        OUTPUT_DIR,
        f"human_pos_{i:03d}.wav"
    )

    with wave.open(filename, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(audio.tobytes())

    print(f"Saved: {filename}")

print()
print("=" * 55)
print("DONE")
print("=" * 55)
print(f"Saved {NUM_SAMPLES} human recordings to:")
print(OUTPUT_DIR)