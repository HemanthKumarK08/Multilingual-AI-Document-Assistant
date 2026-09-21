# Open Decisions & Guide Discussion Points

This document outlines key technical decisions and trade-offs that have been analyzed and assigned recommended defaults, but should be reviewed with the academic project guide prior to commencing implementation.

---

## Decision Log and Review Points

### Decision 1: Primary LLM Generation Backend & Decoupled Configuration
- **Context:** The system requires an LLM for context-grounded multilingual synthesis from retrieved English chunks.
- **Architectural Resolution:** Decouple the generation layer behind an abstract `LLMProvider` interface configurable via `.env` (`LLM_PRIMARY_PROVIDER=gemini|groq|ollama`, `LLM_MODEL_NAME`, `LLM_TEMPERATURE=0.0`).
- **Recommended Default:** Hosted **Google Gemini 1.5 Flash API** as primary (free, high multilingual fluency, 0 local RAM overhead) with **Local Ollama (Llama-3.2-3B)** as offline fallback.

---

### Decision 2: Big Data Telemetry Scale & Data Integrity
- **Context:** Real live testing produces modest query counts during demos; Apache Spark needs substantial data volume to demonstrate distributed processing.
- **Architectural Resolution:** Categorize all telemetry logs under 4 sources (`REAL_APPLICATION`, `SYNTHETIC_SIMULATION`, `EVALUATION_BENCHMARK`, `ERROR_DIAGNOSTIC`). Bundle an automated simulation generator (`scripts/generate_telemetry_dataset.py`) generating 50,000–100,000 events, with explicit labeling on the admin dashboard.
- **Recommended Default:** Clearly labeled synthetic dataset for PySpark scale demonstration without misrepresenting real student traffic.

---

### Decision 3: Language Rollout Sequence & Telugu Positioning
- **Context:** Prioritizing Indic languages across the development lifecycle.
- **Architectural Resolution:** Strict staged implementation order: (1) English, (2) Hindi, (3) Kannada, (4) Telugu (Staged regional expansion evaluated in Stage 14), and (5) Romanized Code-Mixed input (Kanglish/Hinglish subword matching).
- **Recommended Default:** Core MVP focuses on English, Hindi, Kannada, and code-mixed queries; Telugu benchmarked during Stage 14 evaluation.

---

### Decision 4: Authentication Architecture for Single-Institution Scope
- **Context:** Securing admin routes without overengineering enterprise IAM.
- **Architectural Resolution:** Public anonymous read-only access for students; HTTP Bearer Session Token authentication with PBKDF2 password hashing for Document Administrators.
- **Recommended Default:** PBKDF2 hashed SQLite/env credentials with 8-hour session lifetime.

---

### Decision 5: Voice Interaction Scope (Speech-to-Text / Text-to-Speech)
- **Context:** Audio querying and spoken answers.
- **Architectural Resolution:** Strictly isolated as an optional, non-blocking enhancement (Stage 17) using browser-native Web Speech API.
- **Recommended Default:** Browser Web Speech API as an optional presentation feature.
