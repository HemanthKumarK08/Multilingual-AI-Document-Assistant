# Project Boundaries: In-Scope vs. Out-of-Scope

To ensure high academic quality, timely delivery, and clear defense criteria for this MCA project, this document establishes the explicit operational boundaries of the system.

---

## 1. Explicitly In-Scope

The following features, modules, and workflows are strictly committed as part of the core project:

1. **Multi-Format Document Ingestion:** Administrative upload and parsing of digital `.pdf`, `.docx`, and `.txt` institutional regulatory files.
2. **Page-Aware Text Chunking:** Extraction with preserved page-level metadata and chunk indexing.
3. **Multilingual Dense Vector Storage:** Local embedded vector database (ChromaDB) powered by pre-trained multilingual embedding models (`multilingual-e5-small` / `paraphrase-multilingual-mpnet-base-v2`).
4. **Cross-Lingual Information Retrieval:** Retrieval of English source text chunks in response to queries written in English, Kannada, Telugu, Hindi, and Romanized Code-Mixed text (Kanglish/Hinglish).
5. **Context-Grounded LLM Generation:** Evidence-gated prompt architecture that enforces strict factual compliance with retrieved context, reduces hallucination risk, and provides verifiable document name and page number citations.
6. **Deterministic Negative Fallback:** Outputting an explicit *"Information Not Found"* notification when user queries cannot be verified against uploaded documents.
7. **Structured Telemetry Collection:** JSON Lines event logging capturing query text, detected language, retrieval similarity scores, latencies, and fallback flags.
8. **Big Data Batch Analytics with Apache Spark:** Distributed batch ETL and statistical aggregation using PySpark on multi-core local execution, processing high-volume query and document telemetry datasets.
9. **Administrative Analytics & Document Management UI:** Interactive web dashboard displaying document status, query trend graphs, language usage distributions, unanswered query clusters, and latency profiles.
10. **Quantitative Evaluation Suite:** Automated benchmarking harness computing HitRate@K, MRR@K, Faithfulness, and Latency percentiles on a golden test dataset.

---

## 2. Explicitly Out-of-Scope

The following capabilities are deliberately excluded to prevent scope creep, unrealistic operational promises, and architectural bloat:

1. **General Web Knowledge & Real-Time Internet Browsing:** The system will NOT search the public internet or answer queries outside the scope of uploaded institutional documents.
2. **Legal, Financial, or Medical Advisory:** The system is an informational assistant and will not perform statutory legal interpretation or binding financial calculation beyond verbatim document policies.
3. **Automated Administrative Decision-Making:** The system will not automatically approve attendance exemptions, grant scholarships, or alter student records.
4. **Handwritten Document OCR & Complex Scanned Image Restoration:** Ingesting handwritten notes, illegible scans, or non-digital photocopies is excluded from V1 core scope.
5. **Universal Support for All Global Languages:** Language capabilities are strictly scoped to English, Kannada, Telugu, Hindi, and their respective Romanized code-mixed forms.
6. **Voice Recognition for Complex Regional Accents / Low-Resource Dialects:** Real-time conversational speech-to-text for rare dialects or noisy environments is excluded; only standard browser-level STT is considered as an optional bonus.
7. **Multi-Node Distributed Cloud Spark Clusters (AWS EMR / Databricks):** Big Data processing is designed and benchmarked for local distributed multi-core execution (`local[*]`), avoiding cloud infrastructure costs.
8. **Enterprise Single Sign-On (SSO / LDAP / SAML Multi-Tenancy):** Institutional user authentication is kept lightweight (session/token passkey) to focus engineering effort on AI/ML and Big Data components.
9. **Guaranteed 100% Zero-Hallucination SLA:** While prompt guardrails and thresholding drastically minimize hallucinations, theoretical elimination of all generative drift cannot be guaranteed by any contemporary LLM architecture.

---

## 3. Boundary Enforcement Matrix

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             SYSTEM BOUNDARIES                               │
├──────────────────────────────────────┬──────────────────────────────────────┤
│               IN-SCOPE               │             OUT-OF-SCOPE             │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ • Uploaded Digital PDFs, DOCX, TXT   │ • Real-time Internet Web Search      │
│ • English, Kannada, Telugu, Hindi    │ • Universal Translation of 100+ Langs│
│ • Verifiable Page Citations          │ • Binding Legal / Financial Advice   │
│ • Deterministic Fallback on Unknowns │ • Handwritten Document OCR           │
│ • PySpark Batch Telemetry Analytics  │ • Paid Cloud Spark Cluster (EMR)     │
│ • Local CPU Execution on Laptop      │ • Dedicated Server GPUs (CUDA)       │
└──────────────────────────────────────┴──────────────────────────────────────┘
```
