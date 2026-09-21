# Stakeholders and User Roles Specification

## 1. Stakeholder Identification

The project interacts with several distinct academic and institutional entities:

1. **Student Body (Primary Beneficiary):** Seeks quick, reliable, multi-lingual answers to institutional policy questions without having to comb through dense PDF circulars.
2. **Institutional Administration & Department Staff:** Uploads and maintains official circulars, handbooks, examination notifications, and seeks empirical data on student information demands.
3. **Academic Evaluators & Project Guides:** Evaluates the technical soundness, software engineering architecture, RAG quality, Big Data pipeline integrity, and academic rigor of the project.
4. **System Maintainer / Developer:** Operates, configures, evaluates, monitors, and optimizes the RAG retrieval pipeline, vector indexes, and PySpark analytics jobs.

---

## 2. User Roles & Detailed Responsibilities

### 2.1 Role 1: Student / General User (End User)
- **Primary Goal:** Submit natural language questions in English, Kannada, Telugu, Hindi, or Code-Mixed text and receive grounded, accurate answers with citations.
- **Key Actions & Capabilities:**
  - Enter natural language queries via text box (and optional future voice input).
  - Select target query/response language or rely on automatic language detection.
  - View grounded AI-generated answers.
  - Inspect exact source document citations (Document Title, Clause/Section, Page Number, and source excerpt).
  - Receive clear notifications when information is not present in institutional files.
  - Provide binary feedback (Thumbs Up / Thumbs Down / Issue Reported) to log response quality.
- **Constraints & Restrictions:**
  - Strictly read-only access.
  - No permission to upload, modify, re-index, or delete institutional documents.
  - No direct access to raw vector embeddings or backend administrative analytics.

### 2.2 Role 2: Document Administrator (Institutional Admin)
- **Primary Goal:** Maintain the veracity of the institutional knowledge base and monitor student information needs.
- **Key Actions & Capabilities:**
  - Upload official institutional documents (PDF, DOCX, TXT) across distinct categories (Academic Regulations, Examinations, Scholarships, Hostel, Placements, General Circulars).
  - View ingestion status (Uploaded, Extracting, Chunked, Embedded, Indexed, Failed).
  - View document metadata (File size, upload date, total pages, total chunks generated, SHA-256 hash).
  - Activate, deactivate, or delete outdated circulars to prevent obsolete policies from being retrieved.
  - Access the PySpark-generated Analytics Dashboard to inspect query trends, language distributions, unanswered questions, and document retrieval frequencies.
- **Constraints & Restrictions:**
  - Cannot alter low-level ML model weights or underlying vector indexing algorithms.
  - Limited to institutional administrative scope.

### 2.3 Role 3: System Administrator / Developer (Technical Role)
- **Primary Goal:** Configure, maintain, evaluate, and benchmark system components.
- **Key Actions & Capabilities:**
  - Configure embedding model parameters, chunking parameters (chunk size, chunk overlap), and similarity search thresholds ($k$, distance metrics).
  - Configure LLM backend options (Local quantized model vs. Hosted API model).
  - Trigger PySpark batch telemetry aggregation jobs manually or via scheduled tasks.
  - Run offline evaluation pipelines (Recall@K, Hit Rate, Faithfulness, Latency benchmarks).
  - Inspect application logs, error traces, and vector database integrity.
- **Delivery Mechanism:** For Version 1 (Academic MVP), this role operates primarily via environment configuration files (`.env`, `config.yaml`), CLI scripts, and developer inspection endpoints.

---

## 3. Role-Based Permissions Matrix

| Feature / Action | Student / General User | Document Administrator | System Administrator / Dev |
| :--- | :---: | :---: | :---: |
| **Submit Text Query (Multilingual)** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **View Grounded Answer & Citations** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **Submit Query Quality Feedback** | ✅ Full Access | ✅ Full Access | ✅ Full Access |
| **Upload Documents (PDF, DOCX, TXT)** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **View Ingestion Status & File List** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **Activate / Deactivate / Delete Docs** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **View PySpark Analytics Dashboard** | ❌ Denied | ✅ Full Access | ✅ Full Access |
| **Trigger Batch PySpark ETL Jobs** | ❌ Denied | ⚠️ Trigger Button | ✅ CLI / Automated |
| **Configure RAG / Embeddings / LLM** | ❌ Denied | ❌ Denied | ✅ Config / CLI |
| **Run Offline Evaluation Harness** | ❌ Denied | ❌ Denied | ✅ CLI Harness |

---

## 4. Mandatory vs. Optional Roles for Version 1

### Mandatory for Version 1 (Core Scope)
1. **Student / General User (Public Access):** The primary front-facing interface for text-based multilingual document QA with citation display. **Access Model:** Completely public, anonymous, read-only access (no login or registration required).
2. **Document Administrator (Protected Access):** Administrative interface enabling authenticated document upload, file status management, index maintenance, and visualization of PySpark analytics summaries. **Access Model:** HTTP Basic Auth or Bearer session token authentication using PBKDF2-HMAC-SHA256 hashed credentials stored in SQLite / configured via `.env` (`ADMIN_USERNAME`, `ADMIN_PASSWORD_HASH`, `ADMIN_SECRET_KEY`).
3. **System Administrator / Developer (CLI & Config):** Operates configuration files (`.env`, `config.yaml`), triggers offline evaluation scripts, and runs diagnostic tools.

### Explicitly Out-of-Scope Authentication Features (Deferred Past V1)
- **Enterprise Multi-Tenant IAM:** Single Sign-On (SSO), LDAP, SAML 2.0, Active Directory integration, and student user accounts/logins are explicitly deferred to focus on core AI/ML, multilingual RAG, and Big Data analytics.
