"""
Language Detection & Normalization.
Supported: English (en), Hindi (hi), Kannada (kn) - configurable.
"""
import re
from typing import Optional
from backend.app.config import get_settings

# Unicode ranges for Indic scripts
DEVANAGARI_RANGE = (0x0900, 0x097F)
KANNADA_RANGE = (0x0C80, 0x0CFF)


def detect_script(text: str) -> Optional[str]:
    """Detects primary script from unicode codepoints."""
    devanagari_count = 0
    kannada_count = 0
    latin_count = 0

    for char in text:
        cp = ord(char)
        if DEVANAGARI_RANGE[0] <= cp <= DEVANAGARI_RANGE[1]:
            devanagari_count += 1
        elif KANNADA_RANGE[0] <= cp <= KANNADA_RANGE[1]:
            kannada_count += 1
        elif ('a' <= char <= 'z') or ('A' <= char <= 'Z'):
            latin_count += 1

    if devanagari_count > latin_count and devanagari_count > kannada_count:
        return "hi"
    if kannada_count > latin_count and kannada_count > devanagari_count:
        return "kn"
    if latin_count > 0:
        return "en"
    return None


def detect_language(text: str, audio_hint: Optional[str] = None) -> str:
    """
    Resolves language using audio hint and text script/keywords.
    Falls back to DEFAULT_LANG.
    """
    settings = get_settings()
    if audio_hint and audio_hint in settings.supported_languages_list:
        return audio_hint

    script_lang = detect_script(text)
    if script_lang and script_lang in settings.supported_languages_list:
        return script_lang

    # Check for common Hinglish tokens
    hinglish_tokens = ["dawa", "dawakhana", "goli", "subah", "shaam", "roz", "dard", "leta", "khata", "khoon"]
    words = set(re.findall(r'\b\w+\b', text.lower()))
    if any(t in words for t in hinglish_tokens) and "hi" in settings.supported_languages_list:
        return "hi"

    return settings.DEFAULT_LANG

