# Multilingual Query Processing and Script Analysis

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 6 — Multilingual and Code-Mixed Processing Optimization  
**Module:** `app/services/retrieval/query_processing.py`  

---

## 1. Overview

The query processing subsystem serves as the entry point for all user interactions. It accepts raw input strings in English, Hindi (Devanagari), Kannada, Telugu, Romanized Indic dialects (Hinglish, Kanglish, Tenglish), or code-mixed formats, standardizing them into a structured, validated `ProcessedQuery` model.

---

## 2. Deterministic Unicode Normalization Pipeline

The normalization routine `normalize_query_text(raw_query: str) -> str` enforces the following transformations:

1. **Unicode NFC Composition:** Applies `unicodedata.normalize("NFC", raw_query)` to eliminate decomposed Unicode character artifacts (such as separated diacritics and vowels in Indic scripts).
2. **Control Character Stripping:** Removes non-printable ASCII/Unicode control characters while explicitly preserving zero-width non-joiners (`\u200C`) and zero-width joiners (`\u200D`) required for valid Indic conjunct representations.
3. **Symbol & Numeric Preservation:** Retains numeric digits (`0-9`, Indic numerals), percentage signs (`%`), currency symbols (`₹`, `$`), math symbols, punctuation (`?`, `.`, `!`, `-`), and brackets.
4. **Whitespace Standardization:** Replaces carriage returns, newlines, and tabs with single spaces, collapses contiguous spaces, and strips leading/trailing whitespace.
5. **Idempotence Property:**
   $$\text{normalize}(\text{normalize}(q)) = \text{normalize}(q)$$

---

## 3. Script Distribution & Classification

The script distribution analyzer `compute_script_distribution(text: str) -> Dict[str, float]` inspects each character's Unicode codepoint across defined ranges:
- **Latin Block:** `0x0041-0x005A`, `0x0061-0x007A`, `0x00C0-0x017F`
- **Devanagari Block:** `0x0900-0x097F`
- **Kannada Block:** `0x0C80-0x0CFF`
- **Telugu Block:** `0x0C00-0x0C7F`

### Script Classification Decision Rules
- If $\text{ratio}(\text{Devanagari}) > 0.50 \implies \text{Script} = \text{Devanagari}, \text{Language} = \text{hi}$
- If $\text{ratio}(\text{Kannada}) > 0.50 \implies \text{Script} = \text{Kannada}, \text{Language} = \text{kn}$
- If $\text{ratio}(\text{Telugu}) > 0.50 \implies \text{Script} = \text{Telugu}, \text{Language} = \text{te}$
- If $\text{ratio}(\text{Latin}) > 0.50 \implies \text{Script} = \text{Latin}$ (Sub-analyzed for Romanized Indic)
- If multiple non-Latin scripts or Latin + Indic $> 0.15 \implies \text{Script} = \text{Mixed}, \text{is\_code\_mixed} = \text{True}$

---

## 4. Romanized and Code-Mixed Query Detection

To prevent misclassifying Romanized Indic queries as standard English, `detect_romanized_language()` checks token membership against curated functional marker vocabularies:

- **Hindi Functional Markers:** *kitna, kitne, kab, kya, kaise, kahan, hota, hai, lagega, karna, chahiye, mein, ke, ki, se, nahi*
- **Kannada Functional Markers:** *eshtu, yestu, enu, beku, agutte, ide, illa, hege, yelli, madabeku, irabeku, ge, alli, inda, na*
- **Telugu Functional Markers:** *entha, emiti, ela, undali, undi, ledu, ekkada, chesukovali, ivvabaduthundi, untundi, gurinchi, cheyadaniki*

When a Latin-script query contains verified functional markers with confidence $\ge 0.20$, the query is classified with its true linguistic identity (e.g. `language="kn"`, `is_romanized=True`, `is_code_mixed=True`), enabling downstream transliteration and cross-lingual query variant generation.
