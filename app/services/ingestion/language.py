"""
Language and Script Detection Utility Module
Deterministic, CPU-first script analyzer using Unicode character range frequency distributions.
"""

from typing import NamedTuple, Dict
from app.services.ingestion.constants import SupportedLanguage, ScriptType

class LanguageDetectionResult(NamedTuple):
    language: str
    script: str
    confidence: float
    detection_method: str
    notes: str | None = None

# Unicode Block Ranges
UNICODE_RANGES = {
    ScriptType.DEVANAGARI: range(0x0900, 0x097F + 1),
    ScriptType.KANNADA: range(0x0C80, 0x0CFF + 1),
    ScriptType.TELUGU: range(0x0C00, 0x0C7F + 1),
    # Latin Basic & Extended ranges
    ScriptType.LATIN: (
        list(range(0x0041, 0x005A + 1)) +
        list(range(0x0061, 0x007A + 1)) +
        list(range(0x00C0, 0x00FF + 1)) +
        list(range(0x0100, 0x017F + 1))
    )
}

# Set of Latin range ints for fast O(1) lookup
_LATIN_CODEPOINTS = set(UNICODE_RANGES[ScriptType.LATIN])
_DEVANAGARI_RANGE = (0x0900, 0x097F)
_KANNADA_RANGE = (0x0C80, 0x0CFF)
_TELUGU_RANGE = (0x0C00, 0x0C7F)

# Common high-frequency English stopwords for Latin language confirmation
_ENGLISH_MARKERS = {
    "the", "and", "is", "in", "to", "of", "for", "with", "academic", "student",
    "students", "college", "course", "examination", "semester", "attendance",
    "shall", "rules", "policy", "regulations", "fee", "hostel", "placement"
}

def detect_script_and_language(text: str | None) -> LanguageDetectionResult:
    """
    Analyzes character distribution across Unicode blocks to identify primary script and language.
    
    Returns:
        LanguageDetectionResult containing (language, script, confidence, detection_method, notes).
    """
    if not text or not text.strip():
        return LanguageDetectionResult(
            language=SupportedLanguage.UNKNOWN.value,
            script=ScriptType.UNKNOWN.value,
            confidence=0.0,
            detection_method="unicode_script_frequency",
            notes="Empty or whitespace-only text"
        )

    # Count characters in each script
    script_counts: Dict[str, int] = {
        ScriptType.DEVANAGARI.value: 0,
        ScriptType.KANNADA.value: 0,
        ScriptType.TELUGU.value: 0,
        ScriptType.LATIN.value: 0,
    }
    total_alphabetic_chars = 0

    for char in text:
        cp = ord(char)
        if _DEVANAGARI_RANGE[0] <= cp <= _DEVANAGARI_RANGE[1]:
            script_counts[ScriptType.DEVANAGARI.value] += 1
            total_alphabetic_chars += 1
        elif _KANNADA_RANGE[0] <= cp <= _KANNADA_RANGE[1]:
            script_counts[ScriptType.KANNADA.value] += 1
            total_alphabetic_chars += 1
        elif _TELUGU_RANGE[0] <= cp <= _TELUGU_RANGE[1]:
            script_counts[ScriptType.TELUGU.value] += 1
            total_alphabetic_chars += 1
        elif cp in _LATIN_CODEPOINTS:
            script_counts[ScriptType.LATIN.value] += 1
            total_alphabetic_chars += 1

    if total_alphabetic_chars == 0:
        return LanguageDetectionResult(
            language=SupportedLanguage.UNKNOWN.value,
            script=ScriptType.UNKNOWN.value,
            confidence=0.0,
            detection_method="unicode_script_frequency",
            notes="No alphabetic characters identified"
        )

    # Calculate ratios
    ratios = {k: v / total_alphabetic_chars for k, v in script_counts.items()}
    primary_script = max(ratios, key=ratios.get)
    max_ratio = ratios[primary_script]

    # Check for mixed script (e.g. English headings with Kannada body)
    sorted_ratios = sorted(ratios.values(), reverse=True)
    is_mixed = len(sorted_ratios) > 1 and sorted_ratios[1] >= 0.20

    detected_script = ScriptType.MIXED.value if (is_mixed and max_ratio < 0.80) else primary_script

    # Determine language from script
    if primary_script == ScriptType.DEVANAGARI.value:
        lang = SupportedLanguage.HINDI.value
        confidence = round(max_ratio, 2)
        notes = f"Devanagari script ratio: {max_ratio:.2%}"
    elif primary_script == ScriptType.KANNADA.value:
        lang = SupportedLanguage.KANNADA.value
        confidence = round(max_ratio, 2)
        notes = f"Kannada script ratio: {max_ratio:.2%}"
    elif primary_script == ScriptType.TELUGU.value:
        lang = SupportedLanguage.TELUGU.value
        confidence = round(max_ratio, 2)
        notes = f"Telugu script ratio: {max_ratio:.2%}"
    elif primary_script == ScriptType.LATIN.value:
        # Check for English markers in Latin text
        words = {w.lower().strip(".,;:!?()[]\"'") for w in text.split()}
        english_match_count = len(words.intersection(_ENGLISH_MARKERS))
        if english_match_count >= 2:
            lang = SupportedLanguage.ENGLISH.value
            confidence = min(1.0, round(0.70 + (english_match_count * 0.03), 2))
            notes = f"Latin script with {english_match_count} English institutional markers"
        else:
            lang = SupportedLanguage.ENGLISH.value  # Default Latin to English baseline
            confidence = round(max_ratio * 0.75, 2)
            notes = "Latin script (provisional English)"
    else:
        lang = SupportedLanguage.UNKNOWN.value
        confidence = 0.0
        notes = "Indeterminate script"

    return LanguageDetectionResult(
        language=lang,
        script=detected_script,
        confidence=confidence,
        detection_method="unicode_script_frequency",
        notes=notes
    )
