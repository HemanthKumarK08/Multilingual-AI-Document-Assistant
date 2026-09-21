"""
Query Processing and Multilingual Normalization Service (Phase 6)
Deterministic, CPU-first query normalizer, script analyzer, and language classifier.
"""

import re
import unicodedata
from typing import Dict, List, Optional, Tuple

from app.services.ingestion.constants import ScriptType, SupportedLanguage
from app.services.ingestion.language import detect_script_and_language
from app.services.retrieval.exceptions import QueryValidationError
from app.services.retrieval.models import ProcessedQuery

# Indic Unicode ranges
_DEVANAGARI_RANGE = (0x0900, 0x097F)
_KANNADA_RANGE = (0x0C80, 0x0CFF)
_TELUGU_RANGE = (0x0C00, 0x0C7F)

# Romanized functional markers for Indic language detection
_HINDI_ROMANIZED_MARKERS = {
    "kitna", "kitne", "kitni", "kab", "kya", "kaise", "kahan", "hote", "hain",
    "hai", "lagega", "hoga", "karna", "chahiye", "rahega", "par", "mein", "me",
    "ke", "ki", "ko", "se", "nahi", "karo", "diya", "sakta", "sakte", "bhi"
}

_KANNADA_ROMANIZED_MARKERS = {
    "eshtu", "yestu", "enu", "yenu", "beku", "agutte", "aagutte", "ide", "illa",
    "hege", "yelli", "yaavudu", "madabeku", "irabeku", "beka", "ge", "alli",
    "inda", "annu", "na", "matte", "hagadare", "koduva", "thappu"
}

_TELUGU_ROMANIZED_MARKERS = {
    "entha", "yenta", "emiti", "emi", "ela", "undali", "undi", "ledu", "ekkada",
    "chesukovali", "ivvabaduthundi", "untundi", "gurinchi", "kani", "cheyadaniki",
    "vastundi", "chesina", "pedda", "chala"
}


def normalize_query_text(raw_query: str) -> str:
    """
    Applies deterministic, idempotent Unicode normalization and cleaning:
    - Normalizes Unicode to standard NFC form.
    - Preserves zero-width joiners where necessary or standardizes them.
    - Removes non-printable control characters (except standard whitespace).
    - Preserves numbers, percentages (%), currency symbols (₹, $), punctuation (?, ., !, -), and brackets.
    - Collapses repeated whitespace and strips leading/trailing spaces.
    """
    if raw_query is None:
        raise QueryValidationError("Query cannot be None.")

    # 1. Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", raw_query)

    # 2. Clean non-printable control characters while preserving Indic characters and standard whitespace
    cleaned_chars: List[str] = []
    for ch in normalized:
        cat = unicodedata.category(ch)
        # Keep non-control characters, plus allow \u200C (ZWNJ) and \u200D (ZWJ) for Indic ligatures
        if cat.startswith("C") and ch not in ("\u200C", "\u200D", "\t", "\n", "\r"):
            continue
        cleaned_chars.append(ch)
    normalized = "".join(cleaned_chars)

    # 3. Standardize whitespace
    normalized = re.sub(r"[\r\n\t]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if not normalized:
        raise QueryValidationError("Query cannot be empty or whitespace-only.")

    return normalized


def compute_script_distribution(text: str) -> Dict[str, float]:
    """
    Computes exact fractional character distribution across recognized scripts.
    """
    counts = {
        "latin": 0,
        "devanagari": 0,
        "kannada": 0,
        "telugu": 0,
        "other": 0,
    }
    total = 0

    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A or 0x00C0 <= cp <= 0x017F:
            counts["latin"] += 1
            total += 1
        elif _DEVANAGARI_RANGE[0] <= cp <= _DEVANAGARI_RANGE[1]:
            counts["devanagari"] += 1
            total += 1
        elif _KANNADA_RANGE[0] <= cp <= _KANNADA_RANGE[1]:
            counts["kannada"] += 1
            total += 1
        elif _TELUGU_RANGE[0] <= cp <= _TELUGU_RANGE[1]:
            counts["telugu"] += 1
            total += 1
        elif unicodedata.category(ch).startswith("L"):
            counts["other"] += 1
            total += 1

    if total == 0:
        return {k: 0.0 for k in counts}

    return {k: round(v / total, 4) for k, v in counts.items()}


def detect_romanized_language(text: str) -> Tuple[Optional[str], float]:
    """
    Detects whether a Latin-script query is Romanized Hindi, Kannada, or Telugu based on functional markers.
    Returns (detected_lang, confidence).
    """
    tokens = [t.lower() for t in re.findall(r"[a-zA-Z]+", text)]
    if not tokens:
        return None, 0.0

    token_set = set(tokens)
    hi_matches = len(token_set & _HINDI_ROMANIZED_MARKERS)
    kn_matches = len(token_set & _KANNADA_ROMANIZED_MARKERS)
    te_matches = len(token_set & _TELUGU_ROMANIZED_MARKERS)

    max_matches = max(hi_matches, kn_matches, te_matches)
    if max_matches == 0:
        return None, 0.0

    confidence = min(1.0, max_matches / max(1, len(tokens) * 0.4))

    if hi_matches == max_matches and hi_matches > kn_matches and hi_matches > te_matches:
        return "hi", confidence
    elif kn_matches == max_matches and kn_matches > hi_matches and kn_matches > te_matches:
        return "kn", confidence
    elif te_matches == max_matches and te_matches > hi_matches and te_matches > kn_matches:
        return "te", confidence
    elif kn_matches > 0:
        return "kn", confidence
    elif hi_matches > 0:
        return "hi", confidence
    return "te", confidence


def process_query(raw_query: str, explicit_language: Optional[str] = None) -> ProcessedQuery:
    """
    Comprehensive query processor:
    - Normalizes Unicode text (idempotent NFC).
    - Computes script distributions across Latin, Devanagari, Kannada, and Telugu.
    - Detects native Indic language and Romanized/Code-Mixed varieties.
    - Produces a structured ProcessedQuery model.
    """
    normalized = normalize_query_text(raw_query)

    # Compute script distributions
    dist = compute_script_distribution(normalized)

    # Detect primary script
    non_zero_scripts = {k: v for k, v in dist.items() if v > 0.15 and k != "other"}
    if len(non_zero_scripts) > 1:
        primary_script = "Mixed"
    elif dist["devanagari"] > 0.5:
        primary_script = "Devanagari"
    elif dist["kannada"] > 0.5:
        primary_script = "Kannada"
    elif dist["telugu"] > 0.5:
        primary_script = "Telugu"
    elif dist["latin"] > 0.5:
        primary_script = "Latin"
    else:
        primary_script = "Unknown"

    # Detect native script language
    det_result = detect_script_and_language(normalized)
    
    # Check Romanized indicators if Latin or Mixed
    is_romanized = False
    is_code_mixed = False
    detected_romanized_lang, rom_conf = detect_romanized_language(normalized)

    # Determine final language code
    if explicit_language and explicit_language.strip():
        lang = explicit_language.strip().lower()
        lang_source = "explicit"
        if primary_script == "Latin" and lang in ["hi", "kn", "te"]:
            is_romanized = True
    else:
        if primary_script == "Devanagari":
            lang = "hi"
            lang_source = "detected"
        elif primary_script == "Kannada":
            lang = "kn"
            lang_source = "detected"
        elif primary_script == "Telugu":
            lang = "te"
            lang_source = "detected"
        elif primary_script in ("Latin", "Mixed"):
            if detected_romanized_lang and rom_conf >= 0.2:
                lang = detected_romanized_lang
                lang_source = "detected"
                is_romanized = True
                is_code_mixed = True
            else:
                lang = "en"
                lang_source = "detected"
        else:
            lang = det_result.language if det_result.language != "und" else "en"
            lang_source = "default"

    # Code-mixed evaluation
    has_latin = dist.get("latin", 0.0) > 0.1
    has_indic = (dist.get("devanagari", 0.0) + dist.get("kannada", 0.0) + dist.get("telugu", 0.0)) > 0.1
    if has_latin and has_indic:
        is_code_mixed = True
    elif is_romanized:
        is_code_mixed = True

    return ProcessedQuery(
        raw_query=raw_query,
        normalized_query=normalized,
        language=lang,
        script=primary_script,
        language_source=lang_source,
        is_code_mixed=bool(is_code_mixed),
        is_romanized=bool(is_romanized),
        is_transliterated=False,
        script_distribution=dist,
    )
