# Phase 2.3 — Normalization & Language/Script Detection

## 1. Text Normalization Pipeline

The normalization module in [`app/services/ingestion/normalization.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/app/services/ingestion/normalization.py) ensures consistent, deterministic character representation across heterogeneous document sources without corrupting Indian language scripts.

### 1.1 Sequential Transformation Stages:
1. **Unicode NFC Normalization:** Applies standard Unicode Normalization Form C (`unicodedata.normalize("NFC", text)`), composing canonical decomposing pairs into unified characters.
2. **Newline Unification:** Replaces all CRLF (`\r\n`) and classic Mac CR (`\r`) line endings with standard Unix LF (`\n`).
3. **Control Character Stripping:** Removes non-printable control characters in ASCII ranges `0x00-0x08`, `0x0B-0x0C`, `0x0E-0x1F`, and `0x7F-0x9F`, while explicitly preserving tab (`\t` / `0x09`) and newline (`\n` / `0x0A`).
4. **Line-Level Whitespace Trimming:** Strips trailing horizontal spaces from each line.
5. **Horizontal Space Compression:** Collapses 2+ consecutive horizontal spaces into a single space (`[^\S\r\n\t]{2,}` -> ` `).
6. **Excessive Blank Line Collapsing:** Collapses 3 or more consecutive newlines into 2 (`\n{3,}` -> `\n\n`), preserving paragraph separation while eliminating wasted tokens.

### 1.2 Non-Destructive Guardrails:
- **Zero Stemming / Lemmatization:** Preserves exact morphological forms.
- **Zero Stop-Word Removal:** Retains grammatical cohesion necessary for semantic embeddings.
- **Zero Case Lowercasing:** Preserves casing for acronyms (USN, CGPA, VTU, BIT) and named entities.
- **Full Indic Script Fidelity:** Tested on Devanagari (`\u0900-\u097F`), Kannada (`\u0C80-\u0CFF`), and Telugu (`\u0C00-\u0C7F`).

---

## 2. Language & Script Detection Engine

The detection module in [`app/services/ingestion/language.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/app/services/ingestion/language.py) provides CPU-first script and language identification using Unicode block range frequency analysis.

### 2.1 Unicode Block Ranges:

| Script | Codepoint Range | Target Language |
| :--- | :---: | :---: |
| **Devanagari** | `\u0900` – `\u097F` | `hi` (Hindi) |
| **Kannada** | `\u0C80` – `\u0CFF` | `kn` (Kannada) |
| **Telugu** | `\u0C00` – `\u0C7F` | `te` (Telugu) |
| **Latin** | `\u0041`–`\u005A`, `\u0061`–`\u007A`, `\u00C0`–`\u017F` | `en` (English) |

### 2.2 Algorithm & Confidence Scoring:
1. Iterates over codepoints, tallying frequencies across the four script buckets.
2. Computes the ratio of each script over total alphabetic characters:
   $$\text{ratio}_s = \frac{\text{count}_s}{\sum \text{count}}$$
3. If the secondary script accounts for $\ge 20\%$ of alphabetic characters and the primary script is $< 80\%$, assigns `script = "mixed"`.
4. For Latin text, evaluates intersection with high-frequency English institutional tokens (`academic`, `student`, `examination`, `semester`, `attendance`, `hostel`, `placement`, `shall`, `rules`). If matches $\ge 2$, assigns `confidence = min(1.0, 0.70 + 0.03 * matches)`.
5. For Devanagari, Kannada, and Telugu, assigns `confidence = round(max_ratio, 2)`.
6. For empty or non-alphabetic text, safely falls back to `language = "unknown"`, `script = "unknown"`, `confidence = 0.0`.
