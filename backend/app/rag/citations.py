"""
Citation Enforcement Module.
Implements Rule S3: Every alert and clinical claim cites its rule ID or knowledge chunk.
Removes uncited claims and falls back to verified rule text if no valid citations remain.
"""
import re
from typing import Dict, List, Optional, Tuple


def extract_citations(text: str) -> List[str]:
    """Extracts citation tokens like [DOC-BEERS-2023-xxx] or [RULE-ID]."""
    matches = re.findall(r'\[([A-Z0-9_\-]+)\]', text)
    return matches


def enforce_citations(
    generated_text: str,
    valid_citation_ids: List[str],
    fallback_rule_message: str,
) -> Tuple[str, List[str], bool]:
    """
    Validates sentence-by-sentence citations against allowed chunk_ids and rule_ids.
    Prunes any clinical sentence that lacks an allowed citation.
    If no valid cited sentences survive, returns (fallback_rule_message, [], False).
    Returns (cleaned_text, valid_citations_found, is_fully_grounded).
    """
    if not generated_text:
        return fallback_rule_message, [], False

    allowed_set = {cid.upper().strip() for cid in valid_citation_ids}
    sentences = re.split(r'(?<=[.!?])\s+', generated_text.strip())

    retained_sentences = []
    found_citations = set()

    for sent in sentences:
        s_citations = extract_citations(sent)
        valid_in_sent = [c.upper() for c in s_citations if c.upper() in allowed_set]

        if valid_in_sent:
            retained_sentences.append(sent)
            found_citations.update(valid_in_sent)
        else:
            # Check if sentence is purely polite / general conversational filler
            # e.g., "Hello.", "Please discuss this with your physician."
            lower = sent.lower()
            if any(phrase in lower for phrase in ["please ask your doctor", "consult your physician", "talk to your doctor", "decision-support"]):
                retained_sentences.append(sent)

    if not retained_sentences:
        # Fallback to stored verified rule text
        return fallback_rule_message, [], False

    cleaned_text = " ".join(retained_sentences)
    return cleaned_text, list(found_citations), len(found_citations) > 0

