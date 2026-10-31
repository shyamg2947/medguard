"""
PII Detection, Masking, and Restoration Module.
Implements Rule S7: Mask before AI.
Detects:
- Indian phone numbers (+91, 10-digit, spaced/hyphenated)
- Email addresses
- Indian government IDs (Aadhaar 12-digit, PAN 10-character alphanumeric)
- Indian 6-digit PIN codes
- Date of birth formats
- Common person names and honorifics (Shri, Smt, Dr, Mr, Mrs, Ji, etc.)
"""
import re
from typing import Dict, List, Tuple

# Regex patterns
RE_PHONE = re.compile(
    r'(?:(?:\+|00)91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}\b|\b\d{3}[-\s]\d{3}[-\s]\d{4}\b'
)
RE_EMAIL = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
RE_AADHAAR = re.compile(r'\b[2-9]\d{3}[\s-]?\d{4}[\s-]?\d{4}\b')
RE_PAN = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b')
RE_PINCODE = re.compile(r'\b[1-9][0-9]{2}\s?[0-9]{3}\b')
RE_DOB = re.compile(r'\b(?:DOB|dob|Birth|born)[\s:]+\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}\b', re.IGNORECASE)

# Common Indian name tokens & honorific patterns
HONORIFICS = [
    r'\b(?:Shri|Smt|Mr|Mrs|Ms|Dr|Pandit|Master|Kumar|Kumari)\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b',
    r'\bPatient\s+Name[\s:]+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b',
    r'\bName[\s:]+([A-Za-z]+(?:\s+[A-Za-z]+)?)\b',
]


def detect_pii_spans(text: str) -> List[Tuple[int, int, str, str]]:
    """
    Finds all PII occurrences in text.
    Returns list of (start_idx, end_idx, pii_type, matched_str).
    """
    spans: List[Tuple[int, int, str, str]] = []

    # Aadhaar first (before phone to avoid overlapping match)
    for m in RE_AADHAAR.finditer(text):
        spans.append((m.start(), m.end(), "GOV_ID", m.group()))

    # PAN
    for m in RE_PAN.finditer(text):
        spans.append((m.start(), m.end(), "GOV_ID", m.group()))

    # Phone
    for m in RE_PHONE.finditer(text):
        # ensure not already matched as Aadhaar
        if not any(s[0] <= m.start() and m.end() <= s[1] for s in spans):
            spans.append((m.start(), m.end(), "PHONE", m.group()))

    # Email
    for m in RE_EMAIL.finditer(text):
        spans.append((m.start(), m.end(), "EMAIL", m.group()))

    # Pincode
    for m in RE_PINCODE.finditer(text):
        if not any(s[0] <= m.start() and m.end() <= s[1] for s in spans):
            spans.append((m.start(), m.end(), "PINCODE", m.group()))

    # DOB
    for m in RE_DOB.finditer(text):
        spans.append((m.start(), m.end(), "DOB", m.group()))

    # Honorifics / Names
    for pat in HONORIFICS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            name_val = m.group(1) if m.groups() else m.group()
            start = m.start(1) if m.groups() else m.start()
            end = m.end(1) if m.groups() else m.end()
            spans.append((start, end, "PERSON", name_val))

    # Sort spans by start descending to replace cleanly
    spans.sort(key=lambda x: x[0], reverse=True)
    return spans


def mask_pii(text: str) -> Tuple[str, Dict[str, str]]:
    """
    Replaces detected PII with tokens [TYPE_N].
    Returns (masked_text, token_to_original_map).
    """
    if not text:
        return text, {}

    spans = detect_pii_spans(text)
    token_map: Dict[str, str] = {}
    counters: Dict[str, int] = {}
    masked_text = text

    # Remove overlapping spans
    clean_spans: List[Tuple[int, int, str, str]] = []
    last_start = len(text) + 1
    for start, end, p_type, val in spans:
        if end <= last_start:
            clean_spans.append((start, end, p_type, val))
            last_start = start

    for start, end, p_type, val in clean_spans:
        counters[p_type] = counters.get(p_type, 0) + 1
        token = f"[{p_type}_{counters[p_type]}]"
        token_map[token] = val
        masked_text = masked_text[:start] + token + masked_text[end:]

    return masked_text, token_map


def has_pii(text: str) -> bool:
    """
    Quick detector to check if text contains unmasked PII.
    Used as safety assertion before outgoing LLM calls.
    """
    if not text:
        return False
    # If it contains Aadhaar, PAN, Email, or clear Phone numbers
    if RE_EMAIL.search(text) or RE_AADHAAR.search(text) or RE_PAN.search(text) or RE_PHONE.search(text):
        return True
    for pat in HONORIFICS:
        if re.search(pat, text, re.IGNORECASE):
            return True
    return False


def restore_pii(masked_text: str, token_map: Dict[str, str]) -> str:
    """
    Restores masked tokens back to their original values in patient-facing output.
    """
    if not masked_text or not token_map:
        return masked_text
    restored = masked_text
    for token, original in token_map.items():
        restored = restored.replace(token, original)
    return restored

