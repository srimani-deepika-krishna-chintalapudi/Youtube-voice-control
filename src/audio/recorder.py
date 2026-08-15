"""
Local Audio Engine - Robust 16kHz Microphone Streaming & Buffering
"""
import time
import queue
import logging
from collections import deque
from typing import Optional, Tuple
import numpy as np
import sounddevice as sd

from src.config import (
    SAMPLE_RATE,
    CHANNELS,
    CHUNK_SIZE,
    AUDIO_DTYPE,
    MIC_DEVICE_INDEX,
    BUFFER_MAX_SECONDS,
)

logger = logging.getLogger(__name__)


class AudioRecorder:
    """
    Manages low-latency 16 kHz microphone input with ring buffer
    and thread-safe chunk queue for wake-word and STT engines.
    """

    def __init__(
        self,
        sample_rate: int = SAMPLE_RATE,
        channels: int = CHANNELS,
        chunk_size: int = CHUNK_SIZE,
        device_index: Optional[int] = MIC_DEVICE_INDEX,
    ):
        self.sample_rate = sample_rate
        self.channels = channels
        self.chunk_size = chunk_size
        self.device_index = self._resolve_device(device_index)

        # Thread-safe queue for real-time streaming chunks (wake-word)
        self.chunk_queue: queue.Queue = queue.Queue(maxsize=100)

        # Circular ring buffer (stores up to BUFFER_MAX_SECONDS of audio)
        max_chunks = int((BUFFER_MAX_SECONDS * sample_rate) / chunk_size)
        self.ring_buffer = deque(maxlen=max_chunks)

        self.stream: Optional[sd.InputStream] = None
        self._is_running = False

    def _resolve_device(self, preferred_index: Optional[int]) -> Optional[int]:
        """Validates or auto-detects a suitable microphone input device."""
        devices = sd.query_devices()
        
        # Check if preferred index is valid
        if preferred_index is not None:
            if 0 <= preferred_index < len(devices):
                dev = devices[preferred_index]
                if dev.get("max_input_channels", 0) > 0:
                    logger.info(f"Using audio input device [{preferred_index}]: {dev['name']}")
                    return preferred_index

        # Auto-detect default or first input device
        default_in = sd.default.device[0]
        if default_in != -1 and default_in < len(devices):
            logger.info(f"Using default input device [{default_in}]: {devices[default_in]['name']}")
            return default_in

        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                logger.info(f"Fallback input device [{idx}]: {dev['name']}")
                return idx

        logger.warning("No input audio device found!")
        return None

    def _audio_callback(self, indata, frames, time_info, status):
        """Low-latency callback executed by sounddevice on incoming audio."""
        if status:
            logger.warning(f"Audio stream status warning: {status}")

        # Flatten to 1D int16 array
        audio_chunk = np.squeeze(indata).astype(np.int16)

        # Store in circular ring buffer
        self.ring_buffer.append(audio_chunk.copy())

        # Push to real-time wake-word queue (drop oldest if full to avoid backpressure)
        try:
            self.chunk_queue.put_nowait(audio_chunk)
        except queue.Full:
            try:
                self.chunk_queue.get_nowait()
                self.chunk_queue.put_nowait(audio_chunk)
            except Exception:
                pass

    def start(self):
        """Starts the microphone input stream."""
        if self._is_running:
            return

        self.stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=AUDIO_DTYPE,
            blocksize=self.chunk_size,
            device=self.device_index,
            callback=self._audio_callback,
        )
        self.stream.start()
        self._is_running = True
        logger.info("Microphone stream started.")

    def stop(self):
        """Stops the microphone stream and releases resources."""
        if not self._is_running:
            return

        self._is_running = False
        if self.stream is not None:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        logger.info("Microphone stream stopped.")

    def get_chunk(self, timeout: float = 0.5) -> Optional[np.ndarray]:
        """
        Retrieves the next real-time 80ms audio chunk for wake-word inference.
        Returns None if timed out.
        """
        try:
            return self.chunk_queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def record_command(self, duration_sec: float) -> np.ndarray:
        """
        Collects continuous audio for duration_sec (for STT).
        Includes the most recent ~0.4s from ring buffer to capture seamless one-breath commands.
        """
        num_chunks = int(duration_sec * self.sample_rate / self.chunk_size)
        chunks = []
        
        # Prepend last 5 chunks (~400ms) from ring buffer
        with self.chunk_queue.mutex:
            recent_chunks = list(self.ring_buffer)[-5:] if len(self.ring_buffer) >= 5 else list(self.ring_buffer)
            chunks.extend(recent_chunks)
            self.chunk_queue.queue.clear()

        remaining_chunks = max(0, num_chunks - len(chunks))
        for _ in range(remaining_chunks):
            chunk = self.get_chunk(timeout=1.0)
            if chunk is not None:
                chunks.append(chunk)
            else:
                break

        if chunks:
            return np.concatenate(chunks)
        return np.array([], dtype=np.int16)

    @staticmethod
    def calculate_rms(chunk: np.ndarray) -> float:
        """Calculates Root Mean Square (RMS) volume level of an audio chunk."""
        if chunk is None or len(chunk) == 0:
            return 0.0
        return float(np.sqrt(np.mean(chunk.astype(np.float32) ** 2)))

    @property
    def is_running(self) -> bool:
        return self._is_running
