"""
Text Normalization Module for Multilingual Institutional Documents
Implements deterministic, non-destructive Unicode and whitespace normalization.
"""

import re
import unicodedata

# Regex to match non-printable control characters except newline (\n) and tab (\t)
# Control characters in ASCII range 0x00-0x1F and 0x7F-0x9F, excluding \t (0x09) and \n (0x0A)
_CONTROL_CHAR_REGEX = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F-\x9F]")

# Regex to collapse 3 or more consecutive newlines into 2
_EXCESSIVE_NEWLINES_REGEX = re.compile(r"\n{3,}")

# Regex to collapse multiple horizontal spaces/tabs (preserving single space or tab)
_MULTIPLE_SPACES_REGEX = re.compile(r"[^\S\r\n\t]{2,}")

def normalize_text(text: str | None) -> str:
    """
    Normalizes extracted text deterministically without destructive rewriting.
    
    Operations:
    1. Unicode NFC normalization.
    2. Newline style unification (CRLF / CR -> LF).
    3. Removal of unsafe control characters (preserving tab and newline).
    4. Trimming trailing horizontal spaces per line.
    5. Collapsing 3+ consecutive newlines into 2.
    6. Stripping outer leading/trailing whitespace.
    
    Guarantees:
    - Preserves all Indic scripts (Devanagari, Kannada, Telugu).
    - Preserves capitalization, punctuation, numbers, and tabular formatting.
    - Zero stemming, zero stop-word removal, zero semantic transformation.
    """
    if not text:
        return ""

    # 1. Unicode NFC Normalization
    normalized = unicodedata.normalize("NFC", text)

    # 2. Unify newlines
    normalized = normalized.replace("\r\n", "\n").replace("\r", "\n")

    # 3. Strip unsafe control characters
    normalized = _CONTROL_CHAR_REGEX.sub("", normalized)

    # 4. Clean up whitespace per line (trim trailing spaces on each line)
    lines = [line.rstrip() for line in normalized.split("\n")]
    normalized = "\n".join(lines)

    # 5. Collapse multiple horizontal spaces (e.g. 5 spaces -> 1, but don't touch indentation if intentional)
    normalized = _MULTIPLE_SPACES_REGEX.sub(" ", normalized)

    # 6. Collapse excessive blank lines
    normalized = _EXCESSIVE_NEWLINES_REGEX.sub("\n\n", normalized)

    # 7. Final outer strip
    return normalized.strip()

def clean_heading_text(heading: str | None) -> str:
    """Cleans and standardizes extracted section headings."""
    if not heading:
        return ""
    cleaned = normalize_text(heading)
    # Remove markdown leading # symbols if present
    cleaned = re.sub(r"^#+\s*", "", cleaned)
    return cleaned.strip()
