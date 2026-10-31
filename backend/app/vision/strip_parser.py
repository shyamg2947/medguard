"""
Medicine Strip and Bottle Image Parser.
Extracts brand, ingredient, strength, and expiry from medicine packaging OCR.
"""
import re
from typing import Any, Dict, List, Optional
from backend.app.entities.resolver import resolve_medication_query
from backend.app.vision.ocr import get_ocr_provider


def parse_medicine_strip(image_path_or_bytes: Any) -> Dict[str, Any]:
    """
    Parses a medicine strip image.
    Returns candidate medications with per-field confidence.
    """
    ocr_provider = get_ocr_provider()
    ocr_res = ocr_provider.extract_text(image_path_or_bytes)
    raw_text = ocr_res["text"]
    lines = ocr_res.get("lines", [])

    # Extract expiry if present
    expiry = None
    exp_match = re.search(r'\b(?:exp|expiry|exp\.)[:\s]+([0-9]{1,2}[\/\-][0-9]{2,4})\b', raw_text, re.IGNORECASE)
    if exp_match:
        expiry = exp_match.group(1)

    # Resolution via entity matcher
    res = resolve_medication_query(raw_text, asr_confidence=ocr_res.get("avg_confidence", 0.9))

    return {
        "raw_ocr_text": raw_text,
        "ocr_confidence": ocr_res.get("avg_confidence", 0.9),
        "expiry": expiry,
        "resolution": res,
    }

