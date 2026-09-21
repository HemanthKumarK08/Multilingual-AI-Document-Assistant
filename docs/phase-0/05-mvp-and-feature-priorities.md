# MVP Definition & Feature Prioritization Matrix

## 1. MVP (Minimum Viable Product) Definition

The Minimum Viable Product for the **Multilingual AI Document Assistant with Big Data Analytics** is designed to validate the end-to-end architecture and deliver core academic value within practical constraints.

### Core MVP Deliverables:
1. **Admin Document Ingestion:** Upload digital PDFs, DOCX, and TXT files with metadata tagging (category, upload date) and automatic page-aware text extraction.
2. **Dense Multilingual Vector Indexing:** Sentence-level chunking with metadata preservation and dense vectorization using a multilingual embedding model (`intfloat/multilingual-e5-small`).
3. **Cross-Lingual Semantic Retrieval:** Vector similarity search supporting English, Hindi, and Kannada queries, with Romanized code-mixed variants, returning top-$K$ chunks with similarity scores.
4. **Context-Grounded LLM Generation:** Evidence-gated prompt synthesis with source citations `[Document Name, Page Number]` and deterministic `"Information Not Found"` fallback when evidence is insufficient (reducing hallucination risk).
5. **Interactive Web Interface:** Clean two-panel layout featuring a Student QA Assistant and an Administrator Document & Analytics portal.
6. **Structured Telemetry & PySpark Analytics:** Ingestion of structured query logs via PySpark, executing batch aggregations to calculate query volume by language, top retrieved circulars, unanswered query clusters, and latency distributions.

### Scope Justification:
- By focusing on text-first RAG and local PySpark analytics, the MVP demonstrates all foundational competencies (NLP, RAG, Information Retrieval, Multilingual AI, Big Data ETL, and Full-Stack Engineering) without getting bogged down in complex speech models, edge-case OCR, or microservices. Telugu is scheduled for staged evaluation immediately following the stabilization of the English/Hindi/Kannada pipeline.

---

## 2. Feature Prioritization Matrix

| Feature / Capability | Priority (MoSCoW) | Academic Value | Technical Complexity | Risk Level | Recommended Phase | Required for Academic Demo? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Admin PDF / DOCX / TXT Upload** | **Must Have** | High | Low-Medium | Low | Stage 3 | **Yes** |
| **Page-Aware Text Extraction & Chunking** | **Must Have** | High | Medium | Low-Medium | Stage 4, 5 | **Yes** |
| **Multilingual Embedding & Vector Search** | **Must Have** | High | Medium | Medium | Stage 6, 7 | **Yes** |
| **English Grounded QA with Page Citations**| **Must Have** | High | Medium | Low | Stage 8, 9 | **Yes** |
| **Deterministic Fallback ("Not Found")** | **Must Have** | High | Low | Low | Stage 9 | **Yes** |
| **Hindi Text QA Support** | **Must Have** | High | Medium | Medium | Stage 10 | **Yes** |
| **Kannada Text QA Support** | **Must Have** | High | Medium | Medium | Stage 10 | **Yes** |
| **Telugu Text QA Support** | **Should Have** | High | Medium | Medium | Stage 10 | **Yes (Evaluation & Staged)** |
| **Code-Mixed Text Queries (Kanglish/Hinglish)** | **Must Have** | Very High | Medium-High | Medium | Stage 10 | **Yes (Subword baseline)** |
| **Categorized Telemetry Logging (JSONL)** | **Must Have** | High | Low | Low | Stage 11 | **Yes** |
| **Synthetic High-Volume Log Generator** | **Must Have** | High | Low | Low | Stage 11 | **Yes (for Spark Scale)** |
| **PySpark Log Aggregation & Analytics** | **Must Have** | Very High | Medium-High | Medium | Stage 12 | **Yes** |
| **Admin Analytics Dashboard Charts** | **Must Have** | High | Medium | Low | Stage 13 | **Yes** |
| **Document Deactivation / Deletion** | **Must Have** | Medium | Low | Low | Stage 3, 6 | **Yes** |
| **Category-Based Filtering** | **Should Have** | Medium | Low | Low | Stage 7 | **Optional Bonus** |
| **Offline Evaluation Benchmark Suite** | **Must Have** | Very High | Medium | Low | Stage 14 | **Yes (for thesis data)** |
| **Browser Speech-to-Text (STT)** | **Could Have** | Medium | Medium | High | Stage 17 | **No (Optional Demo)** |
| **Text-to-Speech (TTS) Output** | **Could Have** | Medium | Low-Medium | Low | Stage 17 | **No (Optional Demo)** |
| **Scanned PDF OCR (Tesseract)** | **Could Have** | Medium | High | High | Future | **No** |
| **Multi-Turn Conversational Memory** | **Could Have** | Medium | Medium | Medium | Future | **No** |
| **Enterprise SSO / LDAP Auth** | **Won't Have (V1)** | Low | High | Low | Future | **No** |

---

## 3. Staged Feature Implementation Plan

```
+-----------------------------------------------------------------------------------+
| STAGE 1: Core Foundation & RAG MVP (Phase 1 & 2)                                  |
| - Text extraction (PDF/DOCX/TXT) with page tracking                              |
| - Chroma/FAISS vector store with Multilingual Embeddings                         |
| - English Q&A with strict citations and deterministic fallback                    |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
| STAGE 2: Multilingual Expansion & Indic RAG (Phase 3)                             |
| - Hindi, Kannada, Telugu, and Romanized Code-Mixed query retrieval validation     |
| - Cross-lingual grounding and localized response generation                       |
| - Expandable raw chunk inspection drawer in UI                                    |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
| STAGE 3: Big Data Telemetry & PySpark Analytics (Phase 4)                         |
| - Structured JSONL telemetry collection (retrieval scores, fallbacks, latency)    |
| - PySpark ETL pipeline (10k-100k events) computing institutional KPI aggregations |
| - Administrator Analytics Dashboard with visual charts & gap reports              |
+------------------------------------------+----------------------------------------+
                                           |
                                           v
+-----------------------------------------------------------------------------------+
| STAGE 4: Academic Evaluation & Optional Enhancements (Phase 5 & 6)               |
| - Empirical RAG evaluation (Recall@K, Hit Rate, Faithfulness, Latency)            |
| - Optional: Web Speech API STT/TTS demonstration                                  |
| - Thesis documentation, user manuals, and project defense package                 |
+-----------------------------------------------------------------------------------+
```
