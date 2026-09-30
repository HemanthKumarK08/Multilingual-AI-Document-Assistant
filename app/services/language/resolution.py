"""
Authoritative Language Resolution & Script Validation Module

Defines the single source of truth for:
1. Response language resolution (priority: explicit -> detected query -> fallback)
2. Script detection from raw queries
3. Positive Unicode script validation for generated answers
4. Standardized language metadata and localized messages
"""
from __future__ import annotations

import re
from typing import Dict, NamedTuple, Optional, Tuple

# Unicode script ranges
_DEVANAGARI_RANGE = (0x0900, 0x097F)
_KANNADA_RANGE = (0x0C80, 0x0CFF)
_TELUGU_RANGE = (0x0C00, 0x0C7F)

# Romanized query lexical markers
_HINDI_ROMANIZED = {"kya", "hai", "kaise", "kab", "kyu", "kyun", "kahan", "kitna", "kitni", "nirdesh", "niyam", "shulk", "yojana"}
_KANNADA_ROMANIZED = {"yenu", "enu", "hege", "yaavaga", "yavaga", "elli", "estu", "eshtu", "yaake", "yake", "shulka", "niyama", "yojane"}
_TELUGU_ROMANIZED = {"emi", "emiti", "ela", "eppudu", "ekkada", "enta", "enduku", "fees", "niyamalu", "pathakam"}

LANGUAGE_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "kn": "Kannada",
    "te": "Telugu",
}

LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "en": "English",
    "hi": "हिन्दी",
    "kn": "ಕನ್ನಡ",
    "te": "తెలుగు",
}

LANGUAGE_UNAVAILABLE_MESSAGES: Dict[str, str] = {
    "hi": "अनुरोधित भाषा (हिन्दी) में उत्तर देने के लिए बहुभाषी मॉडल सेवा वर्तमान में अनुपलब्ध है।",
    "kn": "ವಿನಂತಿಸಿದ ಭಾಷೆಯಲ್ಲಿ (ಕನ್ನಡ) ಉತ್ತರಿಸಲು ಬಹುಭಾಷಾ ಮಾದರಿ ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ.",
    "te": "అభ్యర్థించిన భాషలో (తెలుగు) సమాధానం ఇవ్వడానికి బహుభాషా మోడల్ సేవ ప్రస్తుతం అందుబాటులో లేదు.",
    "en": "Multilingual model inference service is currently unavailable for the requested language.",
}

TTS_LOCALE_MAP: Dict[str, str] = {
    "en": "en-US",
    "hi": "hi-IN",
    "kn": "kn-IN",
    "te": "te-IN",
}


def detect_query_language(text: str) -> str:
    """
    Detect the natural language of a user query based on Unicode script analysis
    and Romanized phonetic keyword markers. Returns 'en', 'hi', 'kn', or 'te'.
    """
    if not text or not text.strip():
        return "en"

    te_count = sum(1 for ch in text if _TELUGU_RANGE[0] <= ord(ch) <= _TELUGU_RANGE[1])
    kn_count = sum(1 for ch in text if _KANNADA_RANGE[0] <= ord(ch) <= _KANNADA_RANGE[1])
    hi_count = sum(1 for ch in text if _DEVANAGARI_RANGE[0] <= ord(ch) <= _DEVANAGARI_RANGE[1])

    max_indic = max(te_count, kn_count, hi_count)
    if max_indic >= 2:
        if te_count == max_indic:
            return "te"
        elif kn_count == max_indic:
            return "kn"
        elif hi_count == max_indic:
            return "hi"

    # Check for Romanized Indic markers
    words = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    te_matches = len(words & _TELUGU_ROMANIZED)
    kn_matches = len(words & _KANNADA_ROMANIZED)
    hi_matches = len(words & _HINDI_ROMANIZED)

    max_rom = max(te_matches, kn_matches, hi_matches)
    if max_rom >= 2:
        if te_matches == max_rom and te_matches > kn_matches and te_matches > hi_matches:
            return "te"
        elif kn_matches == max_rom and kn_matches > hi_matches and kn_matches > te_matches:
            return "kn"
        elif hi_matches == max_rom and hi_matches > kn_matches and hi_matches > te_matches:
            return "hi"

    return "en"


def resolve_response_language(
    explicit_target_language: Optional[str] = None,
    query: Optional[str] = None,
    detected_query_language: Optional[str] = None,
) -> str:
    """
    The single authoritative response language resolution function.
    
    Priority:
      1. Explicit user-selected response language (en, hi, kn, te).
      2. If target is 'auto', None, or empty:
         Use detected query language.
      3. If detection is uncertain:
         Default fallback to 'en'.
    
    Guaranteed return value: exactly one of 'en', 'hi', 'kn', 'te'.
    """
    if explicit_target_language:
        clean = explicit_target_language.lower().strip()
        if clean in ("en", "hi", "kn", "te"):
            return clean

    # Step 2: Auto Detect
    if detected_query_language:
        det_clean = detected_query_language.lower().strip()
        if det_clean in ("en", "hi", "kn", "te"):
            return det_clean

    if query:
        detected = detect_query_language(query)
        if detected in ("en", "hi", "kn", "te"):
            return detected

    return "en"


class ValidationResult(NamedTuple):
    is_valid: bool
    reason: Optional[str] = None

    def __bool__(self) -> bool:
        return bool(self.is_valid)


def validate_target_language_script(text: str, target_lang: str) -> ValidationResult:
    """
    Positive validation that an answer contains genuine text in the target language.
    
    Rules:
    - Telugu (te): Must contain meaningful Telugu characters (U+0C00–U+0C7F).
      Must not be predominantly Latin text. Must not be contaminated with Kannada script.
    - Kannada (kn): Must contain meaningful Kannada characters (U+0C80–U+0CFF).
      Must not be predominantly Latin text. Must not be contaminated with Telugu script.
    - Hindi (hi): Must contain meaningful Devanagari characters (U+0900–U+097F).
      Must not be predominantly Latin text. Must not be contaminated with South Indic scripts.
    - English (en): Accepts standard Latin script. Must not be predominantly Indic script.
    
    Returns:
        ValidationResult(is_valid: bool, violation_reason: Optional[str])
    """
    if not text or not text.strip():
        return ValidationResult(False, "EMPTY_ANSWER")

    target = (target_lang or "en").lower().strip()

    # Clean out URLs, citations, numbers, and punctuation to analyze natural language characters
    cleaned = re.sub(r"https?://\S+|www\.\S+", "", text)
    cleaned = re.sub(r"\[Source \d+\]", "", cleaned)
    cleaned = re.sub(r"\[\d+\]", "", cleaned)
    cleaned = re.sub(r"[\d.,%()\[\]\-:;/\\\"\'\n\r\t]+", "", cleaned)

    latin_letters = sum(1 for ch in cleaned if 0x0041 <= ord(ch) <= 0x005A or 0x0061 <= ord(ch) <= 0x007A)

    if target == "en":
        indic_chars = sum(1 for ch in cleaned if 0x0900 <= ord(ch) <= 0x0D7F)
        if indic_chars > latin_letters and indic_chars >= 20:
            return ValidationResult(False, "INDIC_CONTAMINATION_IN_ENGLISH")
        return ValidationResult(True, None)

    if target == "te":
        te_chars = sum(1 for ch in cleaned if _TELUGU_RANGE[0] <= ord(ch) <= _TELUGU_RANGE[1])
        kn_chars = sum(1 for ch in cleaned if _KANNADA_RANGE[0] <= ord(ch) <= _KANNADA_RANGE[1])
        if kn_chars > 3:
            return ValidationResult(False, "SCRIPT_CONTAMINATION")
        if te_chars < 15:
            return ValidationResult(False, "MISSING_TARGET_SCRIPT")
        # Pure English or pseudo-Indic answers where Latin overwhelmingly dominates over Telugu
        if latin_letters > 2.5 * te_chars and latin_letters > 40:
            return ValidationResult(False, "PREDOMINANTLY_ENGLISH_ANSWER")
        return ValidationResult(True, None)

    if target == "kn":
        kn_chars = sum(1 for ch in cleaned if _KANNADA_RANGE[0] <= ord(ch) <= _KANNADA_RANGE[1])
        te_chars = sum(1 for ch in cleaned if _TELUGU_RANGE[0] <= ord(ch) <= _TELUGU_RANGE[1])
        if te_chars > 3:
            return ValidationResult(False, "SCRIPT_CONTAMINATION")
        if kn_chars < 15:
            return ValidationResult(False, "MISSING_TARGET_SCRIPT")
        if latin_letters > 2.5 * kn_chars and latin_letters > 40:
            return ValidationResult(False, "PREDOMINANTLY_ENGLISH_ANSWER")
        return ValidationResult(True, None)

    if target == "hi":
        hi_chars = sum(1 for ch in cleaned if _DEVANAGARI_RANGE[0] <= ord(ch) <= _DEVANAGARI_RANGE[1])
        s_chars = sum(1 for ch in cleaned if (_TELUGU_RANGE[0] <= ord(ch) <= _TELUGU_RANGE[1]) or (_KANNADA_RANGE[0] <= ord(ch) <= _KANNADA_RANGE[1]))
        if s_chars > 3:
            return ValidationResult(False, "SCRIPT_CONTAMINATION")
        if hi_chars < 15:
            return ValidationResult(False, "MISSING_TARGET_SCRIPT")
        if latin_letters > 2.5 * hi_chars and latin_letters > 40:
            return ValidationResult(False, "PREDOMINANTLY_ENGLISH_ANSWER")
        return ValidationResult(True, None)

    return ValidationResult(True, None)
