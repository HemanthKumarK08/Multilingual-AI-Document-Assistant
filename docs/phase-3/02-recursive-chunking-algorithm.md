# Phase 3 — Recursive Chunking Algorithm

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.chunking.recursive.RecursiveCharacterChunker`

---

## 1. Algorithm Overview

The `RecursiveCharacterChunker` is a stateless, deterministic text splitting algorithm. Rather than rigidly slicing text at arbitrary character boundaries, it attempts to split text along a hierarchy of natural syntactic and semantic delimiters.

```
+-------------------------------------------------------------------------------+
|                             INPUT SOURCE TEXT                                 |
+-------------------------------------------------------------------------------+
                                      |
         +----------------------------+----------------------------+
         |                                                         |
         v                                                         v
 [Length <= chunk_size]                                 [Length > chunk_size]
         |                                                         |
         v                                                         v
Emit Single Chunk [0, len)                           Evaluate Separator Hierarchy:
                                                     1. "\n\n" (Paragraphs)
                                                     2. "\n"   (Line breaks)
                                                     3. ". "   (Sentences)
                                                     4. "? "   (Questions)
                                                     5. "! "   (Exclamations)
                                                     6. "; "   (Semicolons)
                                                     7. ", "   (Commas)
                                                     8. " "    (Words)
                                                     9. ""     (Character fallback)
                                                                   |
                                                                   v
                                                     Select rightmost natural boundary
                                                     in search window [len/3, len]
                                                                   |
                                                                   v
                                                     Emit Chunk [cur_start, actual_end)
                                                                   |
                                                                   v
                                                     Calculate Sliding Overlap:
                                                     - Overlap target: 100 chars
                                                     - Word-boundary alignment
                                                     - Advance cur_start
```

---

## 2. Separator Hierarchy

The separator hierarchy is defined in `app/services/chunking/constants.py`:

```python
DEFAULT_SEPARATORS = [
    "\n\n",   # Multi-paragraph breaks
    "\n",     # Single line breaks
    ". ",     # Sentence boundary (period + space)
    "? ",     # Question boundary
    "! ",     # Exclamation boundary
    "; ",     # Semicolon clause boundary
    ", ",     # Comma phrase boundary
    " ",      # Word boundary
    "",       # Character-level fallback
]
```

### Hierarchy Selection Rationale
1. **Paragraphs (`\n\n`):** Preserves complete thematic units when paragraphs fit within the 600-character ceiling.
2. **Line breaks (`\n`):** Breaks bulleted lists, tabular lines, or stanza-like structures cleanly.
3. **Sentence Boundaries (`. `, `? `, `! `):** Ensures sentences are kept intact wherever possible to maximize embedding semantic coherence.
4. **Phrasal Clauses (`; `, `, `):** Splits complex compound sentences gracefully.
5. **Word Boundaries (` `):** Guarantees words are not severed mid-word.
6. **Character Fallback (`""`):** Guarantees termination even on continuous strings without spaces (e.g., long URLs, hashes, base64 strings).

---

## 3. Sliding-Window Overlap Mechanism

Overlap is applied deterministically between consecutive chunks:
1. When a chunk is emitted ending at `actual_end`, the candidate overlap start is `actual_end - chunk_overlap`.
2. The chunker inspects the candidate overlap slice for a whitespace delimiter to align the overlap start to a clean word boundary.
3. Strict forward-progress guards ensure `next_start > cur_start` and `next_start < actual_end`, preventing infinite loops or duplicate-only chunks.
4. The first chunk of a source unit starts at offset `0` with zero preceding overlap.
5. The final chunk is deduplicated if the overlap slice completely covered the remainder of the text.

---

## 4. Multilingual & Indic Script Preservation

The chunker operates natively on Unicode UTF-8 strings. It handles:
- **Devanagari (Hindi):** Preserves Nukta modifiers, matras, and conjuncts without splitting combining marks.
- **Kannada & Telugu:** Preserves complex ligatures (Virama / Halant attachments) and Dravidian script phonetics.
- **Code-Mixed / Romanized Indic:** Seamlessly splits mixed Latin-Indic phrases along standard word and clause boundaries.
