# Problem Statement & System Definition

## 1. Short Problem Statement

In academic and institutional environments, students, faculty, and administrative staff face significant friction navigating vast, fragmented, and frequently updated policy documents (such as academic regulations, examination bylaws, scholarship circulars, and hostel rules). Existing institutional portals rely on rigid keyword searches or manual PDF scanning, which fail when queries are posed conceptually or in regional Indian languages (Kannada, Telugu, Hindi) and code-mixed dialects (e.g., Kanglish, Tenglish, Hinglish). Furthermore, generic AI chatbots hallucinate policies without verifying institutional text, creating severe compliance and informational risks. There is an urgent need for an AI-powered, multilingual, document-grounded Question Answering (QA) system backed by Big Data analytics that guarantees source-verifiable answers and provides administrators with empirical insights into institutional information gaps and query trends.

---

## 2. Detailed Problem Statement

### 2.1 The Operational Bottleneck in Institutional Information Discovery
Colleges, universities, and technical institutes generate dozens of formal regulatory documents annually, spanning hundreds of pages across multiple administrative departments (Registrar, Academic Dean, Controller of Examinations, Placement Cell, Scholarship Office, Hostel Warden). 
- **Information Fragmentation:** Critical rules (e.g., attendance shortage condonation, detention criteria, fee refund rules, placement eligibility) are dispersed across disparate PDF circulars, handbooks, and meeting minutes.
- **Manual Overhead:** Administrative staff spend disproportionate hours answering repetitive student inquiries, while students frequently miss deadlines or violate policies due to inability to locate exact clauses.

### 2.2 Linguistic Barriers & Code-Mixed Expression
In multi-state educational institutions across India, a substantial proportion of the student demographic is more fluent in regional languages (Kannada, Telugu, Hindi) than formal English.
- Students commonly think and articulate complex regulatory queries in their native language or through code-mixed vernaculars (e.g., *"Hostel re-admission ge minimum attendance percentage eshtu beku?"* or *"Fee refund rule apply avtunda if I withdraw before first semester?"*).
- Existing institutional search engines (Apache Lucene/Elasticsearch or standard CMS search) perform exact keyword matching on English text and completely fail on cross-lingual, semantic, and phonetic transliterations.

### 2.3 The Hallucination Hazard of Generic LLMs
When students turn to generic public Large Language Models (ChatGPT, Claude, etc.) for college advice, the models suffer from fundamental flaws:
- **Lack of Private Context:** Generic LLMs do not possess private institutional circulars and extrapolate general university norms that often contradict specific institutional statutes.
- **Hallucination & Fabrication:** Generic LLMs generate authoritative-sounding but fabricated guidelines, misleading students on critical academic requirements without verification against ground-truth files.
- **Lack of Provenance:** Standard conversational models do not provide verifiable document titles, clause numbers, and page numbers.

### 2.4 Absence of Telemetry & Institutional Analytics
Currently, institutional decision-makers have no visibility into what information students struggle to find.
- Colleges do not know which policies are ambiguous, which circulars generate the most confusion, or how query trends shift before examinations or admission cycles.
- Without a centralized query logging and big data analytics pipeline, institutions cannot proactively improve communication or update confusing regulations.

---

## 3. Existing System vs. Proposed System

| Dimension | Existing System (CMS / PDF Portal / Keyword Search) | Generic Public AI (ChatGPT / Copilot) | Proposed System (Multilingual RAG + PySpark Analytics) |
| :--- | :--- | :--- | :--- |
| **Search Mechanism** | Lexical / Exact keyword matching | Parametric LLM memory | Dense semantic multilingual retrieval + RAG |
| **Document Grounding** | Manual reading of returned PDFs | None (answers from general pre-training) | Strict grounding in institutional vector index |
| **Citation & Auditability** | User must scan entire file manually | Absent or fabricated links | Deterministic page-level and document citations |
| **Language Flexibility** | English-only keyword matching | Multilingual, but no institutional grounding | Cross-lingual retrieval (English, Hindi, Kannada, Telugu, Code-Mixed) |
| **Hallucination Risk** | Low (raw files), but high human error | Extreme risk of policy fabrication | Hallucination-risk reduction via evidence gating & fallback |
| **Handling Missing Data** | Returns 0 search results | Hallucinates plausible answers | Deterministic "Information Not Found" fallback |
| **Institutional Analytics** | Basic page visit counter or zero logs | None (blackbox vendor platform) | Distributed PySpark telemetry ETL & administrative dashboard |

---

## 4. Proposed Solution Architecture (Conceptual)

The proposed system addresses these challenges through a three-tier modular architecture:

```
+-----------------------------------------------------------------------------------+
|                            1. USER INTERFACE LAYER                                |
|   - Multilingual Text Query Input (English, Kannada, Telugu, Hindi, Code-Mixed)   |
|   - Grounded Response Display with Verified Document & Page Citations             |
|   - Admin Document Upload, Processing Telemetry & Analytics Dashboard             |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                        2. MULTILINGUAL RAG CORE PIPELINE                          |
|   +--------------------------+   +-----------------------+   +------------------+ |
|   | Document Ingestion &     |   | Multilingual Dense    |   | Context-Grounded | |
|   | Page-Aware Chunking      |-->| Vector Search         |-->| LLM Generation   | |
|   | (PyMuPDF / docx / txt)   |   | (E5 / MPNet + Vector) |   | (Zero-Halluc.)   | |
|   +--------------------------+   +-----------------------+   +------------------+ |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
|                     3. BIG DATA TELEMETRY & ANALYTICS LAYER                       |
|   - Structured Event Logging (Queries, Latency, Similarity Scores, Fallbacks)     |
|   - Apache Spark / PySpark Batch Processing & Aggregation Engine                  |
|   - Institutional Knowledge Gap Insights, Language Trends & Confusion Heatmaps    |
+-----------------------------------------------------------------------------------+
```

---

## 5. Academic Novelty & Realistic Positioning

To ensure sound academic rigor for an MCA project, the system avoids grandiose claims and focuses on realistic, measurable engineering contributions:

1. **Cross-Lingual Institutional Information Retrieval:** Evaluating and demonstrating how dense multilingual embedding models (`multilingual-e5` / `paraphrase-multilingual-mpnet`) map regional-language (Kannada, Telugu, Hindi) and code-mixed queries to standard English institutional documents without degrading retrieval precision.
2. **Deterministic Grounding & Negative Rejection:** Designing a strict context-bound prompt contract with similarity threshold gating that deterministically outputs `"Information not found in official institutional documents"` when retrieval confidence falls below an empirical threshold.
3. **Conversational Telemetry Analytics via PySpark:** Demonstrating the application of distributed data processing (PySpark) on conversational logs, computing aggregations across high-volume interaction traces (intent clustering, language distribution, retrieval failure patterns, latency percentiles) to produce actionable institutional intelligence.
