# Phase 3 — Validation and Serialization

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Components:** `app.services.chunking.validator.ChunkValidator`, `app.services.chunking.serialization`

---

## 1. Chunk Validation Pipeline

The `ChunkValidator` enforces 8 strict structural and semantic invariants before any chunk artifact is allowed to be serialized to disk.

```
+-------------------------------------------------------------------------------+
|                             CANDIDATE CHUNKS                                  |
+-------------------------------------------------------------------------------+
                                      |
                                      v
  [Check 1] Non-Empty Text          -> Rejects whitespace-only or empty strings
  [Check 2] Length Consistency      -> text_length == len(text_content)
  [Check 3] Stable ID Syntax        -> regex match ^{doc_id}:p{page}:c{idx}$
  [Check 4] Global ID Uniqueness    -> No duplicate chunk IDs within document
  [Check 5] Sequential Continuity   -> chunk_index == 0, 1, 2, ..., N-1
  [Check 6] Page Number Validity    -> page_number >= 1 (1-indexed)
  [Check 7] Offset Invariants       -> 0 <= source_start_offset <= source_end_offset
  [Check 8] Source Token Coverage   -> First, middle, last sample words present
                                      |
                                      v
+-------------------------------------------------------------------------------+
|                       VALIDATED CHUNKED ARTIFACT                              |
+-------------------------------------------------------------------------------+
```

---

## 2. Source Coverage Verification

To mathematically prove that chunking does not silently truncate, lose, or hallucinate document text:
1. Significant content words ($\text{len} > 2$) are extracted from the normalized source text.
2. The validator verifies that anchor tokens sampled across the beginning, middle, and conclusion of the source document appear intact in the emitted chunks.
3. If any anchor token is missing, a `SourceCoverageError` is raised immediately, halting serialization for that document.

---

## 3. Atomic Serialization

All chunk artifacts are serialized to `data/processed/{doc_id}_chunks.json` using atomic file writing:
1. The JSON payload is generated with `indent=2` and `ensure_ascii=False` (preserving native Unicode Devanagari, Kannada, Telugu, and Latin characters).
2. The payload is written to a temporary hidden file: `data/processed/.{doc_id}_chunks.json.tmp`.
3. The temporary file is atomically renamed via `os.replace` (`Path.replace`), guaranteeing that concurrent readers or system interruptions never observe partially written files.
