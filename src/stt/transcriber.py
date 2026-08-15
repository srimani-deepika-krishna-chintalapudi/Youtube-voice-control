"""
Local On-Demand Speech-To-Text Engine
Uses faster-whisper with int8 quantization for ultra-fast local CPU transcription.
"""
import io
import time
import logging
from pathlib import Path
from typing import Union, Optional
import numpy as np
from faster_whisper import WhisperModel

from src.config import (
    WHISPER_MODEL_SIZE,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    MODELS_DIR,
)

logger = logging.getLogger(__name__)


class LocalTranscriber:
    """
    On-demand local speech recognition engine.
    Activated ONLY after a wake-word trigger to preserve CPU & privacy.
    """

    def __init__(
        self,
        model_size: str = WHISPER_MODEL_SIZE,
        device: str = WHISPER_DEVICE,
        compute_type: str = WHISPER_COMPUTE_TYPE,
    ):
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self.download_dir = str(MODELS_DIR / "whisper")

        logger.info(f"Loading faster-whisper model ({model_size}, {device}, {compute_type})...")
        t0 = time.perf_counter()
        self.model = WhisperModel(
            self.model_size,
            device=self.device,
            compute_type=self.compute_type,
            download_root=self.download_dir,
            cpu_threads=4,
        )
        t1 = time.perf_counter()
        logger.info(f"faster-whisper model loaded in {t1 - t0:.2f}s.")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int = 16000) -> str:
        """
        Transcribes a 1D audio array (int16 or float32).
        Returns clean, lowercase transcribed text.
        """
        if audio_data is None or len(audio_data) == 0:
            return ""

        # Convert int16 PCM to float32 [-1.0, 1.0]
        if audio_data.dtype == np.int16:
            audio_float = audio_data.astype(np.float32) / 32768.0
        elif audio_data.dtype == np.float32:
            audio_float = audio_data
        else:
            audio_float = audio_data.astype(np.float32)

        t0 = time.perf_counter()
        # Fast greedy decoding (beam_size=1) with VAD filter to ignore silence
        segments, info = self.model.transcribe(
            audio_float,
            beam_size=1,
            language="en",
            vad_filter=True,
            vad_parameters=dict(min_silence_duration_ms=500),
            without_timestamps=True,
        )

        # Collect segment text
        transcript_parts = [segment.text for segment in segments]
        raw_text = " ".join(transcript_parts).strip()
        t1 = time.perf_counter()

        clean_text = raw_text.lower().strip()
        # Remove common trailing punctuation
        clean_text = clean_text.rstrip(".,!?;:")
        logger.info(f"Transcribed in {t1 - t0:.2f}s: '{clean_text}' (Prob: {info.language_probability:.2f})")
        return clean_text

    def transcribe_file(self, wav_path: Union[str, Path]) -> str:
        """Helper to transcribe a saved WAV file."""
        import scipy.io.wavfile as wavfile
        sr, audio = wavfile.read(str(wav_path))
        return self.transcribe(audio, sample_rate=sr)
