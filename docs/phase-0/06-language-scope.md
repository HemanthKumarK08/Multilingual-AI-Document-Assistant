## 1. Supported Languages & Prioritized Implementation Order

The system targets four primary languages commonly utilized in South Indian and central institutional environments, executed in a strict sequential order:

1. **Phase 1 Priority — English (`en`):** Primary corpus format for official institutional documents; baseline query language.
2. **Phase 2 Priority — Hindi (`hi`):** Devanagari script queries and national circulars; validated for cross-lingual English document retrieval.
3. **Phase 3 Priority — Kannada (`kn`):** Native Kannada script queries and state circulars; core regional language priority for South Indian institutional context.
4. **Phase 4 Priority — Telugu (`te`):** Staged regional expansion. Telugu is implemented and quantitatively evaluated on the golden benchmark dataset after the core English/Hindi/Kannada pipeline is stabilized.
5. **Cross-Cutting Priority — Romanized & Code-Mixed Input (Kanglish / Hinglish / Tenglish):** Subword tokenization mapping for colloquial transliterated queries.

---

## 2. Cross-Lingual RAG Architectural Strategy

In an institutional context, official documents (e.g., VTU/AICTE/Autonomous bylaws) are almost exclusively drafted in formal **English**, while student queries arrive in **Kannada, Telugu, Hindi, or Code-Mixed text**.

To solve this asymmetry without introducing catastrophic translation errors, the system evaluates and implements a **Cross-Lingual Dense Retrieval** architecture:

```
[Student Query in Kannada / Telugu / Hindi / Code-Mixed]
                        │
                        ▼
          [Language & Script Detection]
                        │
                        ├── Native Script (e.g., ಕನ್ನಡ / हिन्दी) ──► Direct Multilingual Dense Embedding
                        └── Romanized Code-Mixed (e.g., Kanglish) ──► Normalization / Query Expansion
                        │
                        ▼
    [Multilingual Embedding Model: intfloat/multilingual-e5-small]
                        │
                        ▼  (Unified Semantic Vector Space)
   [Cross-Lingual Vector Similarity Search over English Chunks]
                        │
                        ▼
   [Top-K English Source Chunks with Verifiable Page Citations]
                        │
                        ▼
      [Multilingual LLM Context-Grounded Generation]
         "Answer the question in [Target Language] 
          using ONLY the provided English context. 
          Cite document and page numbers. 
          If evidence is missing, output NOT_FOUND."
                        │
                        ▼
[Evidence-Grounded Answer in Target Language with Exact Citations & Fallback]
```

> [!IMPORTANT]
> **Hallucination Reality:** While strict prompt guardrails, zero-temperature generation, and similarity threshold gating drastically reduce hallucination risk, no generative LLM architecture can mathematically guarantee 100% elimination of generative variance. Deterministic negative fallback handles unverified questions.

---

## 3. Handling Code-Mixed & Romanized Vernaculars

Students frequently submit queries in Romanized script rather than native Indic scripts:
- **Kanglish:** *"Hostel re-admission ge minimum attendance percentage eshtu beku?"*
- **Hinglish:** *"Exam fee pay karne ki last date kya hai aur late fine kitna lagega?"*
- **Tenglish:** *"Scholarship apply cheyadaniki last date eppudu and eligibility criteria enti?"*

### Processing Strategy for Code-Mixed Input:
1. **Subword Tokenization Advantage:** Modern transformer tokenizers (like WordPiece and SentencePiece used in `xlm-roberta` and `multilingual-e5`) break Romanized terms into phonetic subwords that bridge semantic gaps.
2. **LLM Synthesis Prompting:** Modern state-of-the-art LLMs (Gemini, Llama-3, Mistral) are capable of comprehending code-mixed Indian English and can formulate grammatically sound answers either in clear regional script or structured English with regional terms.

---

## 4. Embedding Model Evaluation for Indic Languages

| Model Identifier | Dimensions | Model Size | CPU Latency | Indic Cross-Lingual Strength | Recommendation |
| :--- | :---: | :---: | :---: | :---: | :--- |
| `intfloat/multilingual-e5-small` | 384 | $\approx 470\text{ MB}$ | $\approx 60\text{ ms}$ | High (supports 100+ languages including KN, TE, HI) | **Top Recommendation (Fast & Accurate)** |
| `sentence-transformers/paraphrase-multilingual-mpnet-base-v2` | 768 | $\approx 1.1\text{ GB}$ | $\approx 180\text{ ms}$ | Very High (rich semantic alignment) | **Alternative (Higher Precision)** |
| `ai4bharat/indic-bert` | 768 | $\approx 500\text{ MB}$ | $\approx 100\text{ ms}$ | High for native scripts, weaker for Romanized | **Secondary Research Baseline** |

---

## 5. Staged Language Rollout Roadmap

1. **Step 1 (MVP Foundation):** English baseline and Hindi (Native Devanagari + Romanized Hinglish).
2. **Step 2 (Regional MVP Core):** Kannada (Native Kannada script + Kanglish).
3. **Step 3 (Staged Regional Expansion & Benchmark Evaluation):** Telugu (Native Telugu script + Tenglish).
4. **Step 4 (Comprehensive Evaluation):** Quantitative benchmarking of Cross-Lingual HitRate@5 and Faithfulness across all 4 language categories and code-mixed variants on the golden benchmark dataset.
