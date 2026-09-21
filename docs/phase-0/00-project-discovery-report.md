# Phase 0: Project Discovery, Scope Definition & Feasibility Analysis Report

**Project Title:** Multilingual AI Document Assistant with Big Data Analytics  
**Subtitle:** An NLP, RAG, and Apache Spark-based system for intelligent document retrieval and multilingual knowledge analytics.  
**Academic Program:** Master of Computer Applications (MCA) Project  
**Author / Candidate:** Hemanth Kumar K  
**Phase:** Phase 0 — Discovery & Feasibility (COMPLETED)  
**Date:** September 2026  

---

## Executive Summary

This report concludes **Phase 0 (Project Discovery, Scope Definition, and Feasibility Analysis)** for the *Multilingual AI Document Assistant with Big Data Analytics*. The primary objective of this phase was to conduct a thorough technical and academic analysis of the problem domain, define a realistic scope achievable on a standard student laptop, establish strict architectural boundaries, evaluate technology trade-offs, and produce a formal project specification guiding all subsequent implementation phases.

The system addresses the widespread challenge in educational institutions where critical regulatory knowledge (academic regulations, examination rules, hostel bylaws, scholarship criteria, placement notices) is fragmented across hundreds of PDF pages and accessible only via rigid keyword searches in English. By combining **Cross-Lingual Retrieval-Augmented Generation (RAG)** with **Apache Spark (PySpark) Big Data Telemetry Analytics**, the project provides students with grounded, multilingual answers backed by verified page citations, while giving administrators data-driven visibility into institutional information gaps and query trends.

---

## Master Discovery & Specification Directory

All formal specifications, requirements, feasibility analyses, and architecture plans produced during Phase 0 are organized within the project documentation suite:

| Document ID & File Name | Document Title & Scope | Primary Purpose |
| :--- | :--- | :--- |
| [01-problem-statement.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/01-problem-statement.md) | **Problem Statement & System Definition** | Academic problem definition, existing system limitations, proposed solution, and novelty. |
| [02-stakeholders-and-user-roles.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/02-stakeholders-and-user-roles.md) | **Stakeholders and User Roles Specification** | Stakeholder analysis, user personas (Student, Admin, Developer), and permissions matrix. |
| [03-functional-requirements.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/03-functional-requirements.md) | **Functional Requirements (MoSCoW)** | 35+ granular functional requirements across Document Ingestion, RAG, Multilingual QA, Big Data, and Admin. |
| [04-non-functional-requirements.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/04-non-functional-requirements.md) | **Non-Functional Requirements Specification** | Measurable benchmarks for latency, vector scaling, reliability, maintainability, and resource constraints. |
| [05-mvp-and-feature-priorities.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/05-mvp-and-feature-priorities.md) | **MVP Scope & Feature Prioritization** | Realistic MVP definition, staged rollout strategy, and feature trade-off analysis. |
| [06-language-scope.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/06-language-scope.md) | **Language Scope & Multilingual Strategy** | Cross-lingual retrieval architecture for English, Kannada, Telugu, Hindi, and Code-Mixed text (Kanglish/Hinglish). |
| [07-document-and-dataset-strategy.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/07-document-and-dataset-strategy.md) | **Document Corpus & Dataset Strategy** | Corpus composition (20–30 docs across 6 domains), metadata schema, golden benchmark design, and privacy guardrails. |
| [08-big-data-analytics-plan.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/08-big-data-analytics-plan.md) | **Big Data Analytics & PySpark Plan** | Telemetry logging schema, synthetic simulation engine (10k–100k events), Spark SQL transformations, and dashboard caching. |
| [09-technology-evaluation.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/09-technology-evaluation.md) | **Technology Evaluation & Stack Selection** | Comparative analysis of FastAPI, ChromaDB, E5-small embeddings, Gemini/Ollama LLM, PySpark, and Vanilla UI. |
| [10-hardware-and-storage-feasibility.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/10-hardware-and-storage-feasibility.md) | **Hardware & Storage Feasibility Analysis** | Detailed RAM budgeting (<4.5 GB peak), disk footprint (<4 GB), CPU-only compatibility, and dual-mode execution. |
| [11-risk-register.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/11-risk-register.md) | **Comprehensive Risk Register & Mitigation** | 20 evaluated risks across RAG, multilingual retrieval, PySpark OOM, LLM rate limits, and scope creep. |
| [12-evaluation-strategy.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/12-evaluation-strategy.md) | **Evaluation Strategy & Benchmarking** | Formal metrics (HitRate@K, MRR@K, Faithfulness, Citation Accuracy), golden dataset schema, and automated test harness. |
| [13-project-boundaries.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/13-project-boundaries.md) | **Project Boundaries: In-Scope vs Out-of-Scope** | Explicit boundaries protecting against scope creep (no web browsing, no handwritten OCR, no paid cloud clusters). |
| [14-development-roadmap.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/14-development-roadmap.md) | **Development Roadmap & 17-Stage WBS** | 17-stage implementation lifecycle with milestones, critical path, and formal exit criteria. |
| [15-open-decisions.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/15-open-decisions.md) | **Open Decisions & Discussion Points** | Trade-offs on LLM provider, Big Data volume simulation, code-mixed handling, and voice features. |
| [16-phase-0-review-and-approval.md](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/16-phase-0-review-and-approval.md) | **Phase 0 Review & Approval Specification** | Formal audit checklist, corrections log, and verified readiness assessment for Phase 1. |

---

## High-Level System Architecture Summary

```
+---------------------------------------------------------------------------------------+
|                                    PRESENTATION LAYER                                 |
|   - Student Multilingual QA Portal (English, Hindi, Kannada, Telugu, Kanglish)        |
|   - Verifiable Source Citations & Raw Context Inspection Drawer                       |
|   - Admin Document Management (Upload, Status, Delete) & Analytics Dashboard          |
+-------------------------------------------+-------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------+
|                           APPLICATION & API SERVICE (FastAPI)                         |
|   +-----------------------+   +------------------------+   +------------------------+ |
|   | Document Ingestion &  |   | Cross-Lingual Semantic |   | Context-Grounded LLM   | |
|   | Page-Aware Chunker    |   | Dense Vector Search    |   | Synthesis & Fallback   | |
|   | (PyMuPDF / docx / txt)|   | (Multilingual-E5-Small)|   | (Gemini / Ollama)      | |
|   +-----------------------+   +------------------------+   +------------------------+ |
|               │                           │                             │             |
|               ▼                           ▼                             ▼             |
|   +-----------------------+   +------------------------+   +------------------------+ |
|   | SQLite Metadata DB    |   | ChromaDB Vector Store  |   | Asynchronous Telemetry | |
|   | (Docs, Status, Config)|   | (Local Persistent HNSW)|   | Event Logger (JSONL)   | |
|   +-----------------------+   +------------------------+   +------------------------+ |
+---------------------------------------------------------------------------------------+
                                            │
                                            ▼
+---------------------------------------------------------------------------------------+
|                         BIG DATA ANALYTICS LAYER (Apache Spark)                       |
|   - PySpark Batch Processing Engine (`local[*]`)                                      |
|   - Ingestion of Categorized Telemetry Logs (Real, Synthetic Simulation, Evaluation)  |
|   - Spark SQL Transformations: Language Share, Knowledge Gaps, Retrieval Latency P95  |
|   - Cached Analytics KPI Summaries consumed instantly by Admin Dashboard              |
+---------------------------------------------------------------------------------------+
```

---

## Core Technical Conclusions & Recommendations

1. **Hardware Feasibility Confirmed:** The entire architecture (FastAPI backend, ChromaDB vector store, Multilingual-E5 embedding model, and PySpark local engine) is budgeted to operate within **$3.5\text{ to }4.5\text{ GB}$ peak RAM**, making it 100% viable on standard 8 GB/16 GB student laptops without requiring a discrete GPU.
2. **Robust Multilingual Retrieval via Dense Cross-Lingual Embeddings:** Direct semantic mapping using `intfloat/multilingual-e5-small` allows regional queries (Hindi, Kannada, Telugu) and Romanized code-mixed inputs (Kanglish, Hinglish) to retrieve English policy chunks without requiring intermediate machine translation steps that distort domain terminology.
3. **Evidence-Gated Prompting & Hallucination-Risk Reduction:** Factual safety is enforced via a dual-gating mechanism: (1) vector similarity thresholding ($\tau$) and (2) strict system prompt grounding with mandatory document and page citations, deterministically outputting *"Information Not Found"* when context is insufficient. Hallucinations are actively minimized although cannot be mathematically eliminated.
4. **Authentic Big Data Contribution via PySpark:** PySpark is used purposefully to process categorized telemetry logs, calculating distributed aggregations and identifying institutional knowledge gaps across high-volume synthetic query histories with clear UI provenance tags.
5. **Clear 17-Stage Roadmap:** The project proceeds strictly across 17 structured implementation stages from architecture and environment setup through database, ingestion, vectorization, grounded RAG, telemetry, PySpark analytics, evaluation, security, and final defense audit.
