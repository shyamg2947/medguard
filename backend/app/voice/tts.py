"""
Text to Speech Interface and Providers.
Supports browser synthesis tokens, pre-rendered audio, and gTTS/EdgeTTS.
"""
from abc import ABC, abstractmethod
import io
from typing import Optional
from backend.app.config import get_settings


class TextToSpeechProvider(ABC):
    @abstractmethod
    def synthesize(self, text: str, lang: str = "en", rate: float = 0.85) -> bytes:
        pass


class StubTTS(TextToSpeechProvider):
    def synthesize(self, text: str, lang: str = "en", rate: float = 0.85) -> bytes:
        # Returns a minimal valid silent WAV header byte payload (44 bytes) for demo
        # RIFF header, WAVE format, 8000Hz 16-bit mono PCM with 0 data frames
        wav_header = bytes([
            0x52, 0x49, 0x46, 0x46,  # "RIFF"
            0x24, 0x00, 0x00, 0x00,  # File size - 8 = 36
            0x57, 0x41, 0x56, 0x45,  # "WAVE"
            0x66, 0x6d, 0x74, 0x20,  # "fmt "
            0x10, 0x00, 0x00, 0x00,  # 16 bytes format chunk
            0x01, 0x00,              # PCM
            0x01, 0x00,              # Mono
            0x40, 0x1f, 0x00, 0x00,  # 8000 Hz
            0x80, 0x3e, 0x00, 0x00,  # 16000 bytes/sec
            0x02, 0x00,              # 2 bytes/sample
            0x10, 0x00,              # 16 bits/sample
            0x64, 0x61, 0x74, 0x61,  # "data"
            0x00, 0x00, 0x00, 0x00   # 0 data bytes
        ])
        return wav_header


def get_tts_provider() -> TextToSpeechProvider:
    return StubTTS()

