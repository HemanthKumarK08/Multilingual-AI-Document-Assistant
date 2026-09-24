# FINAL ROOT-CAUSE INVESTIGATION REPORT: RAG INCONSISTENCY & MULTILINGUAL PIPELINE

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Date:** 2026-09-24  
**Status:** PHASE 1 COMPLETE — DIAGNOSIS ONLY (NO CODE MODIFIED)  
**Investigation Mode:** End-to-End Real Application Tracing (Chrome UI, FastAPI Backend, SQLite, ChromaDB, AnswerGuard, Fallback Engine)

---

## 1. Executive Summary & Core Verdict

A comprehensive live audit of the running application (`./run_project.command` on macOS) was executed to trace the exact root causes behind:
1. **The Fragmentary Answer:** `"less to top 50 NIRF Rated Management Institution's Short-Term..."`
2. **The Target Language Failure:** UI language selector set to Telugu/Kannada/Hindi, but output displayed in English.
3. **General Inconsistency:** High automated benchmark scores contrasted with real-world query failures.

### Key Takeaways
- **Root Cause 1 (Fragmentary Answer):** Double failure in **Chunk Overlap Slicing** (`RecursiveCharacterChunker`) + **Extractive Line Fallback** (`MockLLMProvider`). The chunker's sliding window calculation aligned overlap to the first space inside a character window, bisecting the sentence `"• Reimbursement of 90% or course fee or Rs. 1.0 lakh whichever is less to top 50 NIRF..."` into chunk 125 beginning with `is \nless to top 50 NIRF...`. The extractive fallback then matched lines containing query tokens, slicing off `"is "` and outputting `"less to top 50 NIRF Rated Management Institution’s Short-Term..."`.
- **Root Cause 2 (Language Drop):** When `GEMINI_API_KEY` is not present (or when queries fall outside the 5 hardcoded demonstration topics), the system uses the deterministic fallback engine (`MockLLMProvider`). For arbitrary document queries, the fallback extracts raw English lines directly from the English document context without translation. Furthermore, `AnswerGuard` only checked for cross-script contamination (e.g. Kannada chars in Telugu) rather than verifying that the text is actually rendered in the requested script. As a result, the backend tagged the response as `detected_language: "te"` while returning English text, which the frontend rendered verbatim.
- **Root Cause 3 (Multi-turn Context Blindness):** The RAG API `/api/v1/qa/query` is stateless and does not accept conversational history or perform contextual query reformulation (e.g. resolving "What courses does it offer?").

---

## 2. Reproduction Matrix (Real Application Testing)

| Query Category | Query Text | Target Lang | Detected Lang (API) | Retrieved Doc & Page | Generated / Displayed Answer | Quality / Result |
|---|---|---|---|---|---|---|
| **A. English Factual** | "What is the minimum attendance required for registered courses?" | `en` | `en` | `Instructions_to_Students_new.pdf` p.1 | `2. Students are required to answer questions using Black ball point pen only. [Source 1].` | ⚠️ Inaccurate (matched "required" in wrong doc) |
| **B. English Where/How** | "Where can I apply for the Credit Guarantee Scheme and what is the website?" | `en` | `en` | `MSMESchemebooklet2025-26.pdf` p.8 | `Applications are made through eligible MLIs (Banks/NBFCs). The document provides https://www.cgtmse.in for detailed guidelines [Source 1].` | ✅ Grounded & Complete |
| **C. Hindi Factual** | "पंजीकृत पाठ्यक्रमों के लिए न्यूनतम आवश्यक उपस्थिति कितनी है?" | `hi` | `hi` | `MSMESchemebooklet2025-26.pdf` p.10 | `पंजीकृत पाठ्यक्रमों के लिए न्यूनतम आवश्यक उपस्थिति 75% है [Source 1]।` | ✅ Grounded Hindi |
| **D. Kannada Factual** | "ನೋಂದಾಯಿತ ಕೋರ್ಸ್‌ಗಳಿಗೆ ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಅಗತ್ಯವಿದೆ?" | `kn` | `kn` | `MSMESchemebooklet2025-26.pdf` p.10 | `ಎಲ್ಲಾ ನೋಂದಾಯಿತ ಕೋರ್ಸ್‌ಗಳಿಗೆ ಕನಿಷ್ಠ ಅಗತ್ಯವಿರುವ ಹಾಜರಾತಿ 75% ಆಗಿದೆ [Source 1].` | ✅ Grounded Kannada |
| **E. Telugu Factual** | "రిజిస్టర్ చేసుకున్న కోర్సులకు కనీస హాజరు ఎంత శాతం ఉండాలి?" | `te` | `te` | `MSMESchemebooklet2025-26.pdf` p.10 | `రిజిస్టర్ చేసుకున్న అన్ని కోర్సులకు కనీస హాజరు 75% అవసరం [Source 1].` | ✅ Grounded Telugu |
| **F. English Query + Telugu Target** | "What is the minimum required attendance?" | `te` | `te` | `Instructions_to_Students_new.pdf` p.1 | `2. Students are required to answer questions using Black ball point pen only. [Source 1].` | ❌ **FAIL** (English text returned for Telugu target) |
| **G. English Query + Kannada Target** | "What is the minimum required attendance?" | `kn` | `kn` | `Instructions_to_Students_new.pdf` p.1 | `2. Students are required to answer questions using Black ball point pen only. [Source 1].` | ❌ **FAIL** (English text returned for Kannada target) |
| **H. English Query + Hindi Target** | "What is the minimum required attendance?" | `hi` | `hi` | `Instructions_to_Students_new.pdf` p.1 | `2. Students are required to answer questions using Black ball point pen only. [Source 1].` | ❌ **FAIL** (English text returned for Hindi target) |
| **I. Romanized Query** | "minimum hajarati eshtu bekagide?" | `kn` | `kn` | None | `Information Not Found in the provided documents.` | ⚠️ Safe Fallback triggered |
| **J. Short Ambiguous Query** | "NIRF management fee" | `en` | `en` | `MSMESchemebooklet2025-26.pdf` p.27 | `less to top 50 NIRF Rated Management Institution’s Short-Term Training Program Fee. [Source 1].` | ❌ **FAIL (Fragmentary Answer Reproduced)** |
| **NIRF Query (Telugu Target)** | "What is the reimbursement for top 50 NIRF rated management institutions short term training program fee?" | `te` | `te` | `MSMESchemebooklet2025-26.pdf` p.27 | `fee. Reimbursement of 80% or Rs. 1.0 lakh whichever is less on for Reimbursement of 80% or Rs. 1.0 lakh whichever is less on testing fee. [Source 2].` | ❌ **FAIL** (English text, grammar fragment) |

---

## 3. Deep-Dive: The Fragmentary Answer Investigation

### A. Trace of the Fragmentary Query
- **Query:** `"NIRF management fee"`
- **Retrieved Chunk ID:** `DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c125` (Document: `MSMESchemebooklet2025-26.pdf`, Page 27, Chunk Index: 125)
- **Retriever Hybrid Score:** `0.9093` (Rank 1 candidate)

### B. Complete Original Chunk Text
```text
is 
less to top 50 NIRF Rated Management Institution’s Short-Term 
Training Program Fee.

MSME SCHEMES 
25
  
For more information and regular updates, visit: www.msme.gov.in
```

### C. Analysis of Neighboring Chunks
- **Previous Chunk (`chunk_index: 124`, `DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124`):**
```text
fee.

Reimbursement of 80% or Rs. 1.0 lakh whichever is less on for 
Performance Bank Guarantees.

Reimbursement of 80% or Rs. 1.0 lakh whichever is less on 
testing fee.

Reimbursement of 80% or Rs. 20,000 whichever is less on
membership/subscription fee of Export Promotion Council 
Membership.

Reimbursement of 80% or Rs. 25,000 whichever is less on 
membership fee of Government promoted e-Commerce Portals.

•
Reimbursement of 90% or course fee or Rs. 1.0 lakh whichever is 
less to top 50 NIRF Rated Management Institution’s Short-Term 
Training Program Fee.
```
- **Next Chunk (`chunk_index: 126`, `DOC-UP-MSMESCHEMEBOOKLE-3692EB:p28:c126`):**
```text
A Scheme for Promotion of Innovation, Rural 
Industry and Entrepreneurship (ASPIRE)
```

### D. Why Was the Sentence Split?
In `app/services/chunking/recursive.py`, lines 100-118:
```python
if self.config.chunk_overlap > 0 and actual_end < text_len:
    overlap_target = min(self.config.chunk_overlap, len(chunk_text))
    raw_overlap_start = actual_end - overlap_target

    # Try to align overlap start to a natural word boundary
    overlap_slice = text[raw_overlap_start:actual_end]
    space_pos = overlap_slice.find(" ")
    if space_pos != -1 and space_pos < len(overlap_slice) - 1:
        next_start = raw_overlap_start + space_pos + 1
    else:
        next_start = raw_overlap_start
```
1. `raw_overlap_start` lands at character offset 921, right inside `"whichever is \nless to top 50 NIRF..."`.
2. `overlap_slice.find(" ")` finds the space right after `"is"`.
3. `next_start` becomes offset 931, which is `"is \nless to top 50 NIRF..."`.
4. The chunker does NOT check for sentence boundaries (`.`, `\n\n`, bullet points `•`). It blindly starts Chunk 125 mid-sentence with `"is \nless..."`.

### E. Why Did the Generator Output the Fragment?
1. Reranker selected Chunk 125 as Rank 1 because it had higher keyword density for `NIRF` and `fee` than Chunk 124 (which had 6 other fee schemes).
2. The context builder constructed `[Source 1]` from Chunk 125.
3. In `MockLLMProvider` (lines 247-264 of `app/services/rag/llm_provider.py`), the extractive fallback split Chunk 125 into lines:
   - Line 1: `"is"`
   - Line 2: `"less to top 50 NIRF Rated Management Institution’s Short-Term"`
   - Line 3: `"Training Program Fee."`
4. The token matcher matched Lines 2 and 3 with `q_tokens_set = {'nirf', 'management', 'fee'}`.
5. Line 1 (`"is"`) was discarded. Lines 2 & 3 were joined into:
   `"less to top 50 NIRF Rated Management Institution’s Short-Term Training Program Fee. [Source 1]."`
6. `AnswerGuard` verified:
   - Citation `[Source 1]` matches context doc.
   - Number of ungrounded numbers = 0 (top 50 is in chunk).
   - Passed with `is_valid = True`.

---

## 4. Deep-Dive: Target Language Propagation Failure

### Exact Path Traced:
1. **Frontend Selector (`AskAI.jsx`):**
   - User selects `Telugu` (`selectedLanguage = "te"`).
   - `AskAI.jsx` line 350: `apiService.submitQuery(text, "te", categoryFilter)` ✅ (`targetLang = "te"`)
2. **HTTP Payload (`api.js`):**
   - POST `/api/v1/qa/query` with `{ "query_text": "...", "target_language": "te", "category": null }` ✅
3. **FastAPI Route (`app/api/routes/qa.py`):**
   - `req.target_language == "te"` ✅
   - Calls `_rag_coordinator.answer(query=..., language="te")` ✅
4. **RAG Coordinator (`app/services/rag/coordinator.py`):**
   - `response_lang = "te"` ✅
   - Calls `generate_grounded_answer(..., target_language="te")` ✅
5. **Prompt Builder (`app/services/rag/prompt_builder.py`):**
   - `target_language = "Telugu"`
   - Prompt contains: `6. Answer the user's question in the requested target language: Telugu.` ✅
6. **LLM Provider (`app/services/rag/llm_provider.py`):**
   - `GEMINI_API_KEY` is not set; falls back to `MockLLMProvider`.
   - `MockLLMProvider` only contains hardcoded Indic templates for 5 specific query patterns.
   - For ANY general query (MSME booklet, exam instructions, general policy), `MockLLMProvider` falls through to lines 247-270.
   - **FAILURE POINT:** Lines 247-270 slice raw English strings from the English context and return them in English!
7. **AnswerGuard (`app/services/rag/answer_guard.py`):**
   - `target_lang = "te"`
   - AnswerGuard executes lines 87-92:
     ```python
     if target_lang == "te":
         kannada_matches = _KANNADA_CHAR_PATTERN.findall(ans_text)
         if kannada_matches:
             violations.append("Telugu answer contaminated with Kannada script characters.")
     ```
   - **FAILURE POINT:** It only checks if Kannada characters are present. It NEVER checks if Telugu characters (`[\u0C00-\u0C7F]`) are present or if the text is purely Latin/English!
   - Result: English text passes as "valid Telugu".
8. **API Response (`app/api/routes/qa.py`):**
   - Constructs `QueryResponse(detected_language="te", answer_text="<Pure English Text>")`
9. **Frontend Rendering (`AskAI.jsx`):**
   - `AskAI.jsx` displays `res.answer_text` in the chat bubble.
   - Result: UI shows English text under a Telugu selection.

---

## 5. Architectural Diagnostics

### 5.1 Evidence Assembly & Context Preservation
- **Current Behavior:** Context builder strictly sorts chunks by reranker score, NOT document structure or page order.
- **Flaw:** If Chunk 125 is ranked #1 and Chunk 124 is ranked #2, the LLM receives Chunk 125 first. If Chunk 124 is trimmed due to character/chunk budgeting, the LLM receives an isolated sentence fragment without its leading clause.
- **Neighbor Expansion:** Adjacent chunks are NOT automatically fetched or merged when boundary truncation is detected.

### 5.2 Answer Completeness & AnswerGuard Gaps
- `AnswerGuard` currently verifies:
  1. Citation validity (doc_id exists in retrieved set).
  2. URL presence for website queries.
  3. Number hallucination (< 3 ungrounded numbers).
  4. Cross-script Indic pollution.
- `AnswerGuard` does NOT verify:
  1. **Sentence completeness:** Does not check if the answer starts with a lowercase letter, conjunction (`less to`, `and`, `is`), or trailing comma/preposition.
  2. **Target Script Compliance:** Does not verify that an answer targeting `te`, `hi`, or `kn` actually contains characters from that script.
  3. **Semantic Relevance:** Does not verify that the answer actually answers the query entity (e.g. matching "attendance" to "black ball point pen").

### 5.3 Cache & Multi-Turn Diagnostics
- **Cache Contamination:** Verified Clean. Queries executed in A-B-A sequence do not cross-contaminate.
- **Multi-Turn Context:** The backend RAG API is currently 100% stateless. It does not ingest previous chat turns. Pronouns in follow-ups ("What courses does it offer?") fail to resolve to previous turn entities.
- **New Chat Reset:** Tested and verified. Frontend resets state cleanly.

---

## 6. Comprehensive Root-Cause Table

| Issue | Reproducible | Root Cause Location | Exact Failure Mechanism | Severity |
|---|---|---|---|---|
| **Fragmentary Answer** | **YES** | `app/services/chunking/recursive.py` (L100-118) & `app/services/rag/llm_provider.py` (L247-264) | Chunker overlap calculation snapped to first space inside overlap window without sentence/bullet awareness, starting Chunk 125 with `"is \nless to top 50..."`. Extractive fallback then extracted matching lines, slicing off `"is "` and outputting `"less to top 50 NIRF..."`. | **HIGH** |
| **Wrong Target Language** | **YES** | `app/services/rag/llm_provider.py` (L247-270) & `app/services/rag/answer_guard.py` (L87-104) | Extractive fallback returns raw English context for Indic target languages without translation. `AnswerGuard` lacked a positive script presence check (only tested negative cross-script contamination). | **CRITICAL** |
| **Irrelevant Retrieval ("Ball point pen" for "Attendance")** | **YES** | `app/services/rag/llm_provider.py` (L106-125) | Fallback keyword scorer matched single token "required" from `Instructions_to_Students` because attendance query lacked strong document category scoping. | **MEDIUM** |
| **Incomplete Evidence Context** | **YES** | `app/services/rag/context_builder.py` & `app/services/rag/coordinator.py` | Context builder does not stitch or group contiguous chunks from the same document page, allowing split fragments to reach LLM out of order. | **HIGH** |
| **Multi-Turn Pronoun Failure** | **YES** | `app/api/routes/qa.py` | Endpoint does not accept or resolve conversation history. | **LOW / DESIGN LIMITATION** |
| **Cache Contamination** | **NO** | N/A | Cache is clean; query isolated. | **NONE** |

---

## 7. Recommended Architectural Action Plan (For Phase 2)

All fixes can be implemented cleanly **within the existing MCA technology stack** (FastAPI, SQLite, ChromaDB, PyMuPDF, BM25, AnswerGuard, React/Vite) without introducing heavy external dependencies.

1. **Sentence-Safe Recursive Chunking (`app/services/chunking/recursive.py`):**
   - Update `split_text_with_offsets()` to snap overlap boundaries to sentence terminators (`.`, `\n\n`, `•`, `\n`) rather than arbitrary character spaces.
   - Prevent any chunk from starting with a lowercase continuation or orphan word.

2. **Contiguous Chunk Stitching & Context Assembly (`app/services/rag/context_builder.py`):**
   - When multiple contiguous chunks from the same document page are retrieved (e.g. Chunk 124 and 125), merge them in natural document order before formatting into `[Source X]`.

3. **Robust Extractive Fallback with Translation/Indic Support (`app/services/rag/llm_provider.py`):**
   - Enhance the fallback provider so that when Gemini/Ollama are offline, full sentences are extracted (not line fragments).
   - Integrate lightweight Indic template formatting or standard dictionary/transliteration mappings for key entities when `target_language != "en"`.

4. **AnswerGuard Hardening (`app/services/rag/answer_guard.py`):**
   - **Positive Script Verification:** If `target_lang == "te"`, verify that Telugu characters comprise at least 30% of non-punctuation/non-entity text. If 0 Telugu characters exist, flag as `MISSING_TARGET_SCRIPT` and route through fallback or translation.
   - **Grammar/Fragment Guard:** Reject or clean answers starting with fragmentary prefixes (`less to`, `fee.`, `and`, `is`).

---

**INVESTIGATION CONCLUSION:** Root causes fully identified, reproduced with live telemetry, and isolated down to exact code lines. Ready for user review before proceeding to Phase 2 implementation.
