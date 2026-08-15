import sounddevice as sd
import numpy as np

from openwakeword.model import Model


# ---------------------------------------
# SETTINGS
# ---------------------------------------

SAMPLE_RATE = 16000

# 0.1 second of audio
CHUNK_SIZE = 1600

# Use an existing model only for testing
WAKE_WORD = "hey_jarvis"


# ---------------------------------------
# LOAD MODEL
# ---------------------------------------

print("Loading wake-word model...")

model = Model(
    wakeword_models=[WAKE_WORD],
    inference_framework="onnx"
)

print("Model loaded successfully.")
print()
print("======================================")
print("  WAKE WORD TEST")
print("======================================")
print()
print("Say: Hey Jarvis")
print()
print("Listening...")
print("Press Ctrl+C to stop.")
print()


# ---------------------------------------
# MICROPHONE
# ---------------------------------------

try:

    with sd.InputStream(
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="int16",
        blocksize=CHUNK_SIZE
    ) as stream:

        while True:

            # Read microphone audio
            audio, overflowed = stream.read(CHUNK_SIZE)

            # Convert to numpy array
            audio = np.squeeze(audio)

            # Make sure it's int16
            audio = audio.astype(np.int16)


            # -----------------------------------
            # SEND AUDIO TO WAKE WORD MODEL
            # -----------------------------------

            prediction = model.predict(audio)


            # Get score
            score = prediction.get(WAKE_WORD, 0)


            # -----------------------------------
            # DETECTION
            # -----------------------------------

            if score > 0.5:

                print(
                    f"🔥 WAKE WORD DETECTED! "
                    f"Score: {score:.3f}"
                )

                # Prevent continuous printing
                model.reset()


except KeyboardInterrupt:

    print()
    print("Stopped.")

except Exception as e:

    print()
    print("ERROR:")
    print(e)