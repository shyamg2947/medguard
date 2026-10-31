"""
Speech to Text Interface and Providers.
Supports offline stub (transcript sidecars) and local faster-whisper.
"""
from abc import ABC, abstractmethod
import json
import os
from typing import Any, Dict, List, Optional
from backend.app.config import get_settings


class SpeechToTextProvider(ABC):
    @abstractmethod
    def transcribe(
        self,
        audio_path_or_bytes: Any,
        lang_hint: Optional[str] = None,
        phrase_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Returns: {
            "text": str,
            "language": str,
            "words": [{"w": str, "start": float, "end": float, "conf": float}],
            "avg_conf": float
        }
        """
        pass


class StubSpeechToText(SpeechToTextProvider):
    def transcribe(
        self,
        audio_path_or_bytes: Any,
        lang_hint: Optional[str] = None,
        phrase_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        # If string path provided and sidecar exists, read it
        if isinstance(audio_path_or_bytes, str):
            sidecar = audio_path_or_bytes + ".transcript.json"
            if os.path.exists(sidecar):
                with open(sidecar, "r", encoding="utf-8") as f:
                    return json.load(f)

        # Default fallback transcription
        text = "I am taking Telmisartan 40 mg once daily and Dolo 650 for pain."
        if lang_hint == "hi":
            text = "Main Telmisartan 40 mg roz subah leta hoon aur dard ke liye Dolo 650."

        words = [
            {"w": w, "start": i * 0.5, "end": (i + 1) * 0.5, "conf": 0.95}
            for i, w in enumerate(text.split())
        ]
        return {
            "text": text,
            "language": lang_hint or "en",
            "words": words,
            "avg_conf": 0.95,
        }


class FasterWhisperSTT(SpeechToTextProvider):
    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
            except Exception:
                self._model = False
        return self._model

    def transcribe(
        self,
        audio_path_or_bytes: Any,
        lang_hint: Optional[str] = None,
        phrase_hints: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        model = self._get_model()
        if not model:
            # Fall back to stub if faster_whisper not installed
            return StubSpeechToText().transcribe(audio_path_or_bytes, lang_hint, phrase_hints)

        initial_prompt = ", ".join(phrase_hints) if phrase_hints else None
        segments, info = model.transcribe(
            audio_path_or_bytes,
            language=lang_hint,
            initial_prompt=initial_prompt,
            beam_size=5,
        )

        words = []
        full_text = []
        total_conf = 0.0
        word_count = 0

        for seg in segments:
            full_text.append(seg.text.strip())
            for word in getattr(seg, "words", []):
                words.append({
                    "w": word.word,
                    "start": word.start,
                    "end": word.end,
                    "conf": getattr(word, "probability", 0.9),
                })
                total_conf += getattr(word, "probability", 0.9)
                word_count += 1

        avg_conf = total_conf / max(1, word_count) if word_count else 0.9
        return {
            "text": " ".join(full_text),
            "language": info.language,
            "words": words,
            "avg_conf": avg_conf,
        }


def get_stt_provider() -> SpeechToTextProvider:
    settings = get_settings()
    if settings.MODE == "demo" or settings.STT_PROVIDER == "stub":
        return StubSpeechToText()
    return FasterWhisperSTT(model_size=settings.STT_MODEL_SIZE)

