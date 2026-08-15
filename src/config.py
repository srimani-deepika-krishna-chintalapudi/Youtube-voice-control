"""
Hey YouTube - Configuration Settings
"""
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
SRC_DIR = BASE_DIR / "src"

# Audio Settings
SAMPLE_RATE = 16000          # 16 kHz standard for openWakeWord & faster-whisper
CHANNELS = 1                 # Mono
CHUNK_SIZE = 1280            # 1280 samples = 80ms at 16kHz (openWakeWord native frame size)
AUDIO_DTYPE = "int16"        # 16-bit PCM
MIC_DEVICE_INDEX = 1         # Cirrus Logic High Definition Audio

# Ring Buffer Settings
BUFFER_MAX_SECONDS = 10      # Circular buffer keeps up to 10 seconds of audio in memory

# Wake Word Settings
WAKE_WORD_MODEL_NAME = "hey_youtube"
WAKE_WORD_MODEL_PATH = MODELS_DIR / f"{WAKE_WORD_MODEL_NAME}.onnx"
WAKE_WORD_THRESHOLD = 0.5    # Detection confidence threshold (0.0 to 1.0)
WAKE_WORD_COOLDOWN_SEC = 2.0 # Minimum seconds between wake-word triggers to prevent re-triggering

# Speech-To-Text Settings
WHISPER_MODEL_SIZE = "base.en"  # "tiny.en", "base.en", or "small.en"
WHISPER_DEVICE = "cpu"          # "cpu" or "cuda"
WHISPER_COMPUTE_TYPE = "int8"   # Fast 8-bit integer quantization for low CPU usage
COMMAND_RECORD_SECONDS = 3.5    # Time window to record user voice command after wake-word
COMMAND_SILENCE_TIMEOUT = 1.0   # Stop listening early if silence is detected

# Local WebSocket Server Settings
SERVER_HOST = "127.0.0.1"    # STRICTLY localhost for privacy
SERVER_PORT = 8765           # Port for Chrome Extension communication
