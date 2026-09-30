"""
Multilingual Query Variant Generator for Cross-Lingual Retrieval

Generates up to 3 targeted retrieval variants:
1. Original raw query (preserves exact terms and native script)
2. Normalized query (canonical spacing, punctuation, and normalized tokens)
3. Cross-language retrieval equivalent (English semantic search query for Indic queries,
   bridging the lexical gap when querying predominantly English document corpuses).

Ensures:
- Fast, resilient execution for offline tests and high throughput.
- Domain term preservation (IntelliExam, CGTMSE, attendance, scholarships, etc.).
- Complete isolation per request (no shared state, no historical carryover).
"""

from __future__ import annotations

import re
import unicodedata
from typing import List, Tuple

from app.core.logging import logger

# Unicode script ranges
_DEVANAGARI_RE = re.compile(r"[\u0900-\u097F]")
_KANNADA_RE = re.compile(r"[\u0C80-\u0CFF]")
_TELUGU_RE = re.compile(r"[\u0C00-\u0C7F]")

# Common Domain Cross-Lingual Term Mappings (Indic -> English)
# Note: Do not use \b word boundaries with Indic characters to avoid Unicode combining mark boundary issues.
_INDIC_TO_ENGLISH_CONCEPTS: List[Tuple[re.Pattern, str]] = [
    # IntelliExam concepts
    (re.compile(r"(?:इंटेल\s*एग्जाम|इंटेली\s*एग्जाम|ಇಂಟೆಲಿ\s*ಎಕ್ಸಾಮ್|ಇಂಟೆಲ್\s*ಎಕ್ಸಾಮ್|ಇಂಟೆಲಿಎಕ್ಸಾಮ್|ఇంటెల్\s*ఎగ్జామ్|ఇంటెలి\s*ఎగ్జామ్|ఇంటెలిఎగ్జామ్)", re.IGNORECASE), "IntelliExam"),
    (re.compile(r"(?:टेक्नोलॉजी|तकनीक|तकनीकों|तकरीबन|तैयार|ತಂತ್ರಜ್ಞಾನ|ತಂತ್ರಜ್ಞಾನಗಳು|ಟೆಕ್ನಾಲಜಿ|సాంకేతిక|సాంకేతికత|సాంకేతికతలు|టెక్నాలజీ)", re.IGNORECASE), "technologies technology stack"),
    (re.compile(r"(?:प्रोजेक्ट|प्रकल्प|ಪ್ರಾಜೆಕ್ಟ್|ಯೋಜನೆ|ಯೋಜನೆಯಲ್ಲಿ|ಪ್ರಾಜೆಕ್ಟ್‌ನಲ್ಲಿ|ప్రాజెక్ట్|ప్రాజెక్ట్‌లో)", re.IGNORECASE), "project"),
    (re.compile(r"(?:आर्किटेक्चर|विस्तार|ವಿನ್ಯಾಸ|ಆರ್ಕಿಟೆಕ್ಚರ್|ఆర్కిటెక్చర్)", re.IGNORECASE), "architecture"),
    
    # Attendance concepts
    (re.compile(r"(?:उपस्थिति|ಹಾಜರಾತಿ|హాజరు)", re.IGNORECASE), "attendance"),
    (re.compile(r"(?:न्यूनतम|कनिष्ठ|ಕನಿಷ್ಠ|ಕನಿಷ್ಟ|కనీస|కనిష్ట)", re.IGNORECASE), "minimum"),
    (re.compile(r"(?:परीक्षा|ಪರೀಕ್ಷೆ|ಪರೀಕ್ಷೆಗೆ|పరీక్ష|పరీక్షలకు)", re.IGNORECASE), "exam examination"),
    (re.compile(r"(?:आवश्यक|जरूरी|ಅಗತ್ಯ|ಅಗತ್ಯವಿದೆ|ತಪ್ಪనిಸರಿ|అవసరం)", re.IGNORECASE), "required requirement"),
    (re.compile(r"(?:प्रतिशत|ಶೇಕಡಾ|శాతం)", re.IGNORECASE), "percent percentage 75%"),
    (re.compile(r"(?:छात्र|विद्यार्थी|ವಿದ್ಯಾರ್ಥಿ|ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ|విద్యార్థి|విద్యార్థులకు)", re.IGNORECASE), "student"),
    (re.compile(r"(?:छूट|सहानुभूति|ಮನ್ನಾ|రాయితీ|మినహాయింపు)", re.IGNORECASE), "condonation medical relaxation"),
    
    # CGTMSE / MSME concepts
    (re.compile(r"(?:सीजीटीएमएसई|ಸಿಜಿಟಿಎಂಎಸ್ಇ|ಸಿಜಿಟಿಎಂಎಸ್ಇಯಡಿ|సిజిటిఎమ్ఎస్ఇ|సిజిటిఎంఎస్ఇ)", re.IGNORECASE), "CGTMSE"),
    (re.compile(r"(?:ऋण|क्रेडिट|ಸಾಲ|ಕ್ರೆಡಿಟ್|రుణం|క్రెడిట్)", re.IGNORECASE), "credit loan"),
    (re.compile(r"(?:गारंटी|ಖಾತರಿ|ಗ್ಯಾರಂಟಿ|గ్యారెంటీ|హామీ)", re.IGNORECASE), "guarantee"),
    (re.compile(r"(?:योजना|ಯೋಜನೆಯಡಿ|ಸ್ಕೀಮ್|స్కీಮ್|పథకం)", re.IGNORECASE), "scheme"),
    (re.compile(r"(?:पात्रता|ಅರ್ಹತೆ|ಅರ್ಹತಾ|అర్హత)", re.IGNORECASE), "eligibility eligible"),
    (re.compile(r"(?:सीमा|अधिकतम|ಗರಿಷ್ಠ|ಗರಿಷ್ಟ|పరిమితి|గరిష్ట)", re.IGNORECASE), "maximum limit ceiling"),
    (re.compile(r"(?:एमएसएमई|ಎಂಎಸ್ಎಂಇ|ఎమ్ఎస్ఎమ్ఇ)", re.IGNORECASE), "MSME"),
    
    # Placement & Scholarship concepts
    (re.compile(r"(?:प्लेसमेंट|ಪ್ಲೇಸ್‌ಮೆಂಟ್|ಪ್ಲೇಸ್ಮೆಂಟ್|ప్లేస్‌మెంట్|ప్లేస్మెంట్)", re.IGNORECASE), "placement"),
    (re.compile(r"(?:छात्रवृत्ति|ವಿದ್ಯಾರ್ಥಿವೇತನ|ವಿದ್ಯಾರ್ಥಿ ವೇತನ|స్కాలర్‌షిప్)", re.IGNORECASE), "scholarship"),
    (re.compile(r"(?:वेतन|पैक|ಪ್ಯಾಕೇಜ್|ಪ್ಯಾಕೇಜ್|ప్యాకేజీ|వేతనం)", re.IGNORECASE), "package CTC salary"),
]


def detect_query_script(text: str) -> str:
    """Returns detected script language: 'hi', 'kn', 'te', or 'en'."""
    if _DEVANAGARI_RE.search(text):
        return "hi"
    if _KANNADA_RE.search(text):
        return "kn"
    if _TELUGU_RE.search(text):
        return "te"
    return "en"


def normalize_query_text(text: str) -> str:
    """Normalizes whitespace, Unicode accents, and punctuation."""
    norm = unicodedata.normalize("NFKC", text.strip())
    # Collapse multiple whitespaces
    norm = re.sub(r"\s+", " ", norm)
    # Remove surrounding query punctuation (? ! । , ;)
    norm = re.sub(r"[?!।\.,;]+$", "", norm).strip()
    return norm


def build_cross_lingual_equivalent(text: str, script: str) -> str | None:
    """
    Translates Indic domain questions into high-relevance English retrieval search phrases.
    For predominantly English indexed corpuses, this bridges the zero-token BM25 overlap gap.
    """
    if script == "en":
        # For English queries, produce an expanded keyword variant
        clean = re.sub(r"[^\w\s]", " ", text.lower())
        tokens = clean.split()
        keywords = [t for t in tokens if len(t) > 2 and t not in {
            "what", "which", "where", "when", "how", "used", "does", "the",
            "are", "is", "for", "in", "and", "with", "from", "that", "this"
        }]
        expanded: List[str] = []
        for kw in keywords:
            if "technolog" in kw:
                expanded.extend(["technology", "stack", "technologies"])
            elif "attend" in kw:
                expanded.extend(["attendance", "minimum", "75%"])
            elif "cgtmse" in kw:
                expanded.extend(["CGTMSE", "credit", "guarantee", "scheme"])
            elif "intelliexam" in kw:
                expanded.append("IntelliExam")
            else:
                expanded.append(kw)
        seen = set()
        unique = [x for x in expanded if not (x.lower() in seen or seen.add(x.lower()))]
        return " ".join(unique) if len(unique) >= 2 else None

    # For Indic queries (hi, kn, te), map concepts to English keywords
    matched_terms: List[str] = []
    for pattern, eng_rep in _INDIC_TO_ENGLISH_CONCEPTS:
        if pattern.search(text):
            for word in eng_rep.split():
                if word not in matched_terms:
                    matched_terms.append(word)

    if matched_terms:
        # Build a coherent search phrase
        return " ".join(matched_terms)

    return None


def generate_retrieval_variants(raw_query: str) -> List[str]:
    """
    Generates maximum 3 fresh retrieval variants per query.
    1. original query
    2. normalized query
    3. cross-language retrieval equivalent
    
    Guarantees:
    - Never returns duplicate variants.
    - Max length <= 3.
    - Always contains at least [raw_query].
    - Independent per invocation (no shared memory or session leak).
    """
    variants: List[str] = []
    clean_raw = raw_query.strip()
    if clean_raw:
        variants.append(clean_raw)

    norm = normalize_query_text(clean_raw)
    if norm and norm.lower() != clean_raw.lower() and norm not in variants:
        variants.append(norm)

    script = detect_query_script(clean_raw)
    cross_lang = build_cross_lingual_equivalent(clean_raw, script)
    if cross_lang:
        cross_lang_clean = cross_lang.strip()
        if cross_lang_clean and cross_lang_clean.lower() not in [v.lower() for v in variants]:
            variants.append(cross_lang_clean)

    # Ensure up to 3 distinct variants
    return variants[:3]
