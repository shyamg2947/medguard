"""
Medication Matcher Pipeline.
Implements:
- Indic transliteration & abbreviation expansion with unicode matra preservation
- Exact, RapidFuzz WRatio, Phonetic Metaphone, and n-gram similarity
- Hybrid scoring: 0.5 * string_sim + 0.3 * phonetic_sim + 0.2 * asr_confidence
- Strength & Frequency extraction (English and Hindi/Hinglish)
- Confidence thresholds (ACCEPT >= 0.90, MARGIN >= 0.10, CLARIFY >= 0.65)
"""
import re
import string
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz

from backend.app.config import get_settings
from backend.app.entities.lexicon import INDIC_TRANSLITERATIONS, get_lexicon


def simple_metaphone(word: str) -> str:
    """
    Simplified phonetic encoder for pharmaceutical names.
    Transforms common phonemes (ph->f, c/k->k, th->t, x->ks, etc.)
    """
    if not word:
        return ""
    w = word.lower().strip()
    w = re.sub(r'\bkn|\bgn|\bpn|\bae|\bwr', lambda m: m.group()[1:], w)
    w = w.replace("ph", "f")
    w = w.replace("th", "t")
    w = w.replace("ck", "k")
    w = w.replace("c", "k")
    w = w.replace("x", "ks")
    w = w.replace("z", "s")
    w = w.replace("v", "w")
    w = re.sub(r'[aeiouy]+', '', w[1:]) if len(w) > 1 else w
    res = []
    for char in w:
        if not res or res[-1] != char:
            res.append(char)
    return "".join(res)


def normalize_text(text: str) -> str:
    """Expands abbreviations and normalizes Indic scripts without stripping matras."""
    if not text:
        return ""
    clean_punct = re.sub(r'[.,\/#!$%\^&\*;:{}=\-_`~()?"\']', ' ', text)
    words = clean_punct.split()
    trans_words = []
    for w in words:
        clean_w = w.strip()
        if clean_w in INDIC_TRANSLITERATIONS:
            trans_words.append(INDIC_TRANSLITERATIONS[clean_w])
        else:
            trans_words.append(w)
    norm = " ".join(trans_words).lower()

    abbreviations = {
        r'\btab\b|\btabs\b': 'tablet',
        r'\bcap\b|\bcaps\b': 'capsule',
        r'\bsyp\b|\bsyr\b': 'syrup',
        r'\binj\b': 'injection',
    }
    for pat, rep in abbreviations.items():
        norm = re.sub(pat, rep, norm)

    return norm.strip()


def parse_strength_and_frequency(text: str) -> Tuple[Optional[str], Optional[str], str]:
    """
    Extracts strength (e.g. 40 mg, 650 mg) and frequency (e.g. once daily, subah shaam).
    Returns (strength, frequency, cleaned_drug_phrase).
    """
    raw = text
    strength = None
    frequency = None

    strength_match = re.search(r'\b(\d+(?:\.\d+)?)\s*(mg|mcg|g|ml|iu|k)\b', raw, re.IGNORECASE)
    if strength_match:
        strength = f"{strength_match.group(1)} {strength_match.group(2).lower()}"
        raw = raw[:strength_match.start()] + strength_match.group(1) + raw[strength_match.end():]

    freq_patterns = [
        (r'\b(?:once\s+daily|once\s+a\s+day|od|roz\s+ek\s+baar|roz\s+subah|daily)\b', 'once daily'),
        (r'\b(?:twice\s+daily|twice\s+a\s+day|bd|subah\s+shaam|morning\s+and\s+night)\b', 'twice daily'),
        (r'\b(?:thrice\s+daily|three\s+times\s+a\s+day|tds)\b', 'thrice daily'),
        (r'\b(?:sos|as\s+needed|jab\s+zaroorat\s+ho)\b', 'as needed'),
    ]
    for pat, canonical_freq in freq_patterns:
        m = re.search(pat, raw, re.IGNORECASE)
        if m:
            frequency = canonical_freq
            raw = raw[:m.start()] + raw[m.end():]
            break

    cleaned_name = re.sub(r'\b(?:tablet|capsule|syrup|goli|dawa|take|taking|before|after|breakfast|dinner|bed|time|night|morning)\b', '', raw, flags=re.IGNORECASE)
    cleaned_name = re.sub(r'[^\w\s]', ' ', cleaned_name).strip()
    cleaned_name = re.sub(r'\s+', ' ', cleaned_name)

    return strength, frequency, cleaned_name


def score_candidate(
    query_text: str,
    target_name: str,
    raw_query: str = "",
    asr_confidence: float = 1.0,
    extracted_strength: Optional[str] = None,
) -> float:
    """
    Calculates composite score.
    Gives exact score 1.0 if target is an exact subphrase of the query.
    """
    target_lower = target_name.lower().strip()
    query_lower = query_text.lower().strip()
    raw_lower = raw_query.lower().strip()

    if target_lower == query_lower:
        return 1.0
    if target_lower in raw_lower:
        if re.search(r'\b' + re.escape(target_lower) + r'\b', raw_lower):
            return 1.0

    str_sim = fuzz.WRatio(query_lower, target_lower) / 100.0

    q_meta = simple_metaphone(query_lower)
    t_meta = simple_metaphone(target_lower)
    phon_sim = fuzz.ratio(q_meta, t_meta) / 100.0 if (q_meta and t_meta) else str_sim

    total_score = (0.5 * str_sim) + (0.3 * phon_sim) + (0.2 * asr_confidence)

    if extracted_strength:
        num_str = re.search(r'\d+', extracted_strength)
        if num_str and num_str.group() in target_lower:
            total_score = min(1.0, total_score + 0.10)

    return min(1.0, max(0.0, total_score))


def find_candidates(
    raw_text: str,
    asr_confidence: float = 1.0,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Searches the lexicon for candidate brand and generic matches.
    Returns ranked candidates with scores and margins.
    """
    settings = get_settings()
    lexicon = get_lexicon()
    normalized = normalize_text(raw_text)
    strength, frequency, drug_phrase = parse_strength_and_frequency(normalized)

    if not drug_phrase:
        drug_phrase = normalized

    candidates: List[Dict[str, Any]] = []

    for brand_key, brand_entry in lexicon.brands.items():
        score = score_candidate(
            query_text=drug_phrase,
            target_name=brand_key,
            raw_query=normalized,
            asr_confidence=asr_confidence,
            extracted_strength=strength,
        )
        if score >= 0.40:
            candidates.append({
                "type": "brand",
                "matched_name": brand_entry["brand"],
                "score": score,
                "ingredients": brand_entry["ingredients"],
                "category": brand_entry["category"],
                "form": brand_entry["form"],
                "source": brand_entry["source"],
            })

    for generic_name in lexicon.generics:
        score = score_candidate(
            query_text=drug_phrase,
            target_name=generic_name,
            raw_query=normalized,
            asr_confidence=asr_confidence,
            extracted_strength=strength,
        )
        if score >= 0.40:
            candidates.append({
                "type": "generic",
                "matched_name": generic_name.title(),
                "score": score,
                "ingredients": [{"ingredient": generic_name, "strength": strength or ""}],
                "category": "prescription",
                "form": "tablet",
                "source": "Generic Reference",
            })

    candidates.sort(key=lambda x: x["score"], reverse=True)

    seen = set()
    deduped = []
    for c in candidates:
        name_lower = c["matched_name"].lower()
        if name_lower not in seen:
            seen.add(name_lower)
            deduped.append(c)
        if len(deduped) >= top_k:
            break

    for i, c in enumerate(deduped):
        next_score = deduped[i + 1]["score"] if i + 1 < len(deduped) else 0.0
        c["margin"] = round(c["score"] - next_score, 4)
        c["extracted_strength"] = strength
        c["extracted_frequency"] = frequency
        c["raw_query"] = raw_text

    return deduped
