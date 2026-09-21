# Phase 5 Visual Architecture & Execution Walkthrough

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 5 — Hybrid Retrieval, Reranking, and Grounded RAG Pipeline  
**Document Status:** Audited and Verified  

---

## 1. End-to-End Grounded RAG Architecture

The following diagram illustrates the complete Phase 5 query lifecycle, from raw multilingual/code-mixed user query through dual-path retrieval, heuristic reranking, evidence gating, grounded LLM prompt construction, and citation provenance validation.

```xml
<svg viewBox="0 0 960 620" xmlns="http://www.w3.org/2000/svg" style="background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
  <!-- Definitions & Gradients -->
  <defs>
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#38bdf8"/>
      <stop offset="100%" stop-color="#0284c7"/>
    </linearGradient>
    <linearGradient id="purpleGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#c084fc"/>
      <stop offset="100%" stop-color="#7e22ce"/>
    </linearGradient>
    <linearGradient id="greenGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#4ade80"/>
      <stop offset="100%" stop-color="#15803d"/>
    </linearGradient>
    <linearGradient id="amberGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#fbbf24"/>
      <stop offset="100%" stop-color="#b45309"/>
    </linearGradient>
    <linearGradient id="roseGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#f43f5e"/>
      <stop offset="100%" stop-color="#9f1239"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity="0.4"/>
    </filter>
  </defs>

  <!-- Title -->
  <text x="480" y="40" text-anchor="middle" fill="#f8fafc" font-size="20" font-weight="700">Multilingual Grounded RAG Pipeline Architecture</text>
  <text x="480" y="65" text-anchor="middle" fill="#94a3b8" font-size="13">Phase 5 Hybrid Retrieval, Evidence Gating, and Provenance Verification</text>

  <!-- 1. Query Processing Node -->
  <g transform="translate(40, 100)" filter="url(#shadow)">
    <rect width="200" height="90" rx="10" fill="#1e293b" stroke="url(#blueGrad)" stroke-width="2"/>
    <text x="100" y="32" text-anchor="middle" fill="#38bdf8" font-size="14" font-weight="600">1. Query Processing</text>
    <text x="100" y="55" text-anchor="middle" fill="#cbd5e1" font-size="11">Unicode NFC Normalization</text>
    <text x="100" y="72" text-anchor="middle" fill="#94a3b8" font-size="10">Script &amp; Language Detection</text>
  </g>

  <!-- Arrow to Retrieval -->
  <path d="M 240 145 L 300 145" stroke="#64748b" stroke-width="2" marker-end="url(#arrow)"/>

  <!-- 2. Dual Retrieval Engine Container -->
  <g transform="translate(300, 90)" filter="url(#shadow)">
    <rect width="360" height="170" rx="12" fill="#1e293b" stroke="#334155" stroke-width="2"/>
    <text x="180" y="25" text-anchor="middle" fill="#f1f5f9" font-size="13" font-weight="600">2. Hybrid Retrieval Engine</text>
    
    <!-- Dense Node -->
    <rect x="20" y="40" width="150" height="75" rx="8" fill="#0f172a" stroke="url(#purpleGrad)" stroke-width="1.5"/>
    <text x="95" y="65" text-anchor="middle" fill="#c084fc" font-size="12" font-weight="600">Dense Retrieval</text>
    <text x="95" y="83" text-anchor="middle" fill="#94a3b8" font-size="10">multilingual-e5-small</text>
    <text x="95" y="98" text-anchor="middle" fill="#64748b" font-size="9">ChromaDB Cosine HNSW</text>

    <!-- Lexical Node -->
    <rect x="190" y="40" width="150" height="75" rx="8" fill="#0f172a" stroke="url(#amberGrad)" stroke-width="1.5"/>
    <text x="265" y="65" text-anchor="middle" fill="#fbbf24" font-size="12" font-weight="600">Lexical BM25</text>
    <text x="265" y="83" text-anchor="middle" fill="#94a3b8" font-size="10">In-Memory Token Index</text>
    <text x="265" y="98" text-anchor="middle" fill="#64748b" font-size="9">Unicode Tokenizer</text>

    <!-- Fusion Formula -->
    <text x="180" y="145" text-anchor="middle" fill="#cbd5e1" font-size="11">Weighted Fusion (Dense 0.70 + Lexical 0.30)</text>
  </g>

  <!-- Arrow to Reranker -->
  <path d="M 660 175 L 720 175" stroke="#64748b" stroke-width="2"/>

  <!-- 3. Reranker Node -->
  <g transform="translate(720, 115)" filter="url(#shadow)">
    <rect width="200" height="120" rx="10" fill="#1e293b" stroke="url(#blueGrad)" stroke-width="2"/>
    <text x="100" y="30" text-anchor="middle" fill="#38bdf8" font-size="13" font-weight="600">3. Heuristic Reranker</text>
    <text x="100" y="55" text-anchor="middle" fill="#cbd5e1" font-size="11">Exact Phrase Bonus (+0.12)</text>
    <text x="100" y="73" text-anchor="middle" fill="#cbd5e1" font-size="11">Term Coverage (+0.08)</text>
    <text x="100" y="91" text-anchor="middle" fill="#cbd5e1" font-size="11">Section Match (+0.05)</text>
  </g>

  <!-- Downward Flow to Evidence Gate -->
  <path d="M 820 235 L 820 310 L 680 310" stroke="#64748b" stroke-width="2"/>

  <!-- 4. Evidence Sufficiency Gate -->
  <g transform="translate(420, 270)" filter="url(#shadow)">
    <rect width="260" height="100" rx="10" fill="#1e293b" stroke="url(#roseGrad)" stroke-width="2"/>
    <text x="130" y="28" text-anchor="middle" fill="#f43f5e" font-size="13" font-weight="600">4. Evidence Gate</text>
    <text x="130" y="50" text-anchor="middle" fill="#cbd5e1" font-size="11">Score Threshold &gt;= 0.35</text>
    <text x="130" y="68" text-anchor="middle" fill="#cbd5e1" font-size="11">Injection Keyword Screening</text>
    <text x="130" y="85" text-anchor="middle" fill="#cbd5e1" font-size="11">Candidate Count Verification</text>
  </g>

  <!-- Branch: Gate Pass vs Fail -->
  <path d="M 420 320 L 300 320" stroke="#4ade80" stroke-width="2"/>
  <text x="360" y="312" text-anchor="middle" fill="#4ade80" font-size="10" font-weight="600">SUFFICIENT</text>

  <path d="M 550 370 L 550 460" stroke="#f43f5e" stroke-width="2"/>
  <text x="560" y="420" text-anchor="start" fill="#f43f5e" font-size="10" font-weight="600">INSUFFICIENT</text>

  <!-- Fallback Node -->
  <g transform="translate(430, 460)" filter="url(#shadow)">
    <rect width="240" height="75" rx="10" fill="#1e293b" stroke="url(#roseGrad)" stroke-width="2"/>
    <text x="120" y="28" text-anchor="middle" fill="#f43f5e" font-size="13" font-weight="600">Deterministic Fallback</text>
    <text x="120" y="48" text-anchor="middle" fill="#fca5a5" font-size="10">"Information Not Found..."</text>
    <text x="120" y="64" text-anchor="middle" fill="#94a3b8" font-size="9">Zero Fabricated Citations</text>
  </g>

  <!-- 5. Context Builder & Prompt Construction -->
  <g transform="translate(60, 275)" filter="url(#shadow)">
    <rect width="240" height="95" rx="10" fill="#1e293b" stroke="url(#greenGrad)" stroke-width="2"/>
    <text x="120" y="28" text-anchor="middle" fill="#4ade80" font-size="13" font-weight="600">5. Context &amp; Prompt Builder</text>
    <text x="120" y="50" text-anchor="middle" fill="#cbd5e1" font-size="11">Budget: Top 5, &lt;= 6000 Chars</text>
    <text x="120" y="68" text-anchor="middle" fill="#cbd5e1" font-size="11">Provenance-Labeled Context</text>
    <text x="120" y="85" text-anchor="middle" fill="#94a3b8" font-size="10">Anti-Injection Grounding Guard</text>
  </g>

  <!-- Flow to LLM -->
  <path d="M 180 370 L 180 430" stroke="#64748b" stroke-width="2"/>

  <!-- 6. LLM Provider -->
  <g transform="translate(60, 430)" filter="url(#shadow)">
    <rect width="240" height="85" rx="10" fill="#1e293b" stroke="url(#blueGrad)" stroke-width="2"/>
    <text x="120" y="28" text-anchor="middle" fill="#38bdf8" font-size="13" font-weight="600">6. LLM Inference Layer</text>
    <text x="120" y="50" text-anchor="middle" fill="#cbd5e1" font-size="11">Gemini 1.5 Flash (Cloud API)</text>
    <text x="120" y="68" text-anchor="middle" fill="#94a3b8" font-size="10">Ollama / Mock Offline Fallback</text>
  </g>

  <!-- Flow to Citation Validation -->
  <path d="M 300 472 L 430 472" stroke="#64748b" stroke-width="2"/>

  <!-- Final Output Section -->
  <g transform="translate(710, 430)" filter="url(#shadow)">
    <rect width="210" height="95" rx="10" fill="#1e293b" stroke="url(#greenGrad)" stroke-width="2"/>
    <text x="105" y="28" text-anchor="middle" fill="#4ade80" font-size="13" font-weight="600">7. Validated Response</text>
    <text x="105" y="50" text-anchor="middle" fill="#cbd5e1" font-size="11">Grounded Answer Text</text>
    <text x="105" y="68" text-anchor="middle" fill="#cbd5e1" font-size="11">Verified Chunk Citations</text>
    <text x="105" y="85" text-anchor="middle" fill="#94a3b8" font-size="10">JSONL Telemetry Logged</text>
  </g>

  <path d="M 670 497 L 710 497" stroke="#64748b" stroke-width="2"/>
</svg>
```

---

## 2. Component Reference

| Stage | Module | Key Responsibilities |
|---|---|---|
| **Query Processing** | `app/services/retrieval/query_processing.py` | NFC normalization, script/language classification, token validation |
| **Dense Retrieval** | `app/services/retrieval/dense_retriever.py` | ChromaDB cosine search, `intfloat/multilingual-e5-small` query embedding |
| **Lexical Retrieval** | `app/services/retrieval/lexical_retriever.py` | In-memory Unicode BM25 ranking across corpus chunks |
| **Hybrid Fusion** | `app/services/retrieval/hybrid.py` | Weighted fusion (Dense 0.70 + Lexical 0.30) and score normalization |
| **Heuristic Reranker** | `app/services/retrieval/reranker.py` | Deterministic phrase boost, term coverage, and heading boosts |
| **Evidence Gate** | `app/services/rag/evidence_gate.py` | Pre-generation relevance gating (score $\ge 0.35$), injection checks |
| **Context Builder** | `app/services/rag/context_builder.py` | Chunk assembly, character budgeting ($\le 6000$ chars), source labeling |
| **Prompt Builder** | `app/services/rag/prompt_builder.py` | Factual grounding constraints, anti-override guards, language formatting |
| **LLM Provider** | `app/services/rag/llm_provider.py` | Pluggable interface: Gemini 1.5 Flash, Ollama, and offline Mock provider |
| **Citation Formatter**| `app/services/rag/citation_formatter.py`| Cryptographic and metadata provenance matching to chunk/page/hash |
| **Fallback Handler** | `app/services/rag/fallback.py` | Deterministic "Information Not Found..." fallback generation |
| **Telemetry** | `app/services/telemetry/` | Structured, privacy-safe JSONL query logging (zero raw user data) |

---

## 3. Key Pipeline Guarantees

1. **Deterministic Fallback:** Any query failing the evidence gate or yielding out-of-domain retrieval scores triggers an immediate, unhallucinated information-not-found response with zero fabricated citations.
2. **Provenance Preservation:** All citations returned to clients match indexed chunk IDs, source document filenames, and page offsets verified against Phase 4 vector store records.
3. **Data Privacy Guardrail:** Telemetry logs only request IDs, latencies, detected scripts, candidate counts, and status codes. Raw user questions, prompt contents, retrieved text, and LLM generated answers are never written to telemetry files.
