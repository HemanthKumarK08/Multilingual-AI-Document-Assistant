# Phase 1.5 — Initial Document Corpus Preparation

## 1. Executive Summary

This document details the corpus design, document acquisition and synthesis methodology, directory layout, metadata manifest specification, and validation procedures implemented during Phase 1.5 for the **Multilingual AI Document Assistant with Big Data Analytics**.

The initial corpus serves as the foundational data layer for subsequent text extraction (Phase 2), semantic chunking and multilingual vector embedding (Phase 3), dense/sparse retrieval (Phase 4), and Big Data batch analytics (Phase 7).

---

## 2. Corpus Scope and Category Architecture

The corpus contains **24 realistic institutional documents** partitioned evenly across **6 core institutional categories** (4 documents per category). The categories reflect the administrative, academic, financial, and welfare lifecycle of higher education students:

| Category Code | Category Name | Scope & Content | Document Count | Format | Languages |
| :--- | :--- | :--- | :---: | :--- | :--- |
| `academic_regulations` | Academic Regulations | Degree requirements, grading systems, credit transfer, academic integrity, degree conferral criteria | 4 | Markdown / Digital Text | English (3), Hindi (1) |
| `examination_guidelines` | Examination Guidelines | End-semester examination conduct, hall ticket rules, malpractice penalties, revaluation, backlog rules | 4 | Markdown / Digital Text | English (3), Kannada (1) |
| `attendance` | Attendance & Internal Assessment | Mandatory attendance thresholds, medical leave condonation, Continuous Internal Evaluation (CIE) rules | 4 | Markdown / Digital Text | English (3), Hindi (1) |
| `scholarships` | Scholarships & Financial Aid | Merit-cum-means schemes, fee concessions, government portal integrations, renewal eligibility | 4 | Markdown / Digital Text | English (3), Telugu (1) |
| `hostel` | Hostel & Campus Welfare | Mess rules, curfew timings, room allotment criteria, discipline, anti-ragging policies, grievances | 4 | Markdown / Digital Text | English (3), Kannada (1) |
| `placements` | Placements & Career Services | Campus recruitment eligibility, 'One-Offer' policy, internship attendance, soft skills training, code of conduct | 4 | Markdown / Digital Text | English (3), Hindi (1) |

---

## 3. Language Distribution and Staged Multilingual Strategy

In strict adherence to the **Phase 0 Language Scope** ([`06-language-scope.md`](file:///Users/hemanthkumark/College/BIT/AI:Ml/docs/phase-0/06-language-scope.md)):

```
Total Documents: 24
├── English (en): 18 documents (75.0%) — Primary institutional baseline
├── Hindi (hi):    3 documents (12.5%) — Tier 1 Indian Language
├── Kannada (kn):  2 documents (8.3%)  — Tier 1 State Language (Karnataka)
└── Telugu (te):   1 document  (4.2%)  — Staged expansion / Evaluation sample
```

### Staged Strategy Rationale:
1. **English (75%):** Forms the dense corpus baseline to evaluate core dense vector retrieval, lexical BM25 matching, and reciprocal rank fusion before language drift is introduced.
2. **Hindi & Kannada (20.8%):** Native Indic scripts (Devanagari and Kannada) included to validate script-level tokenization, multilingual embedding alignment (`intfloat/multilingual-e5-small`), and cross-lingual question answering in Phase 3–5.
3. **Telugu (4.2%):** A dedicated financial aid document included as a controlled evaluation target to benchmark multilingual transfer capabilities without over-complicating early pipeline iterations.

---

## 4. Privacy, Licensing, and Provenance Protocol

All documents in the Phase 1 corpus were prepared under rigorous data privacy and governance guardrails:
- **Zero Personally Identifiable Information (PII):** No real student names, USNs (University Seat Numbers), email addresses, phone numbers, or private student records exist in any document.
- **Synthetic Institutional Data:** All documents represent realistic, standard academic policies drafted for demonstration and research purposes under the `academic_demonstration` license.
- **Traceability:** Every document contains clear internal provenance (`internally authored for MCA research benchmarking`).
- **No Web Scraping:** No external websites were scraped, ensuring zero copyright infringement or terms-of-service violations.

---

## 5. Storage Hierarchy and Directory Layout

Documents are physically organized by category under `data/raw/`:

```text
data/raw/
├── corpus_manifest.json
├── academic_regulations/
│   ├── DOC-001-academic-regulations-2024.md
│   ├── DOC-002-credit-transfer-policy.md
│   ├── DOC-003-academic-integrity-code.md
│   └── DOC-004-academic-regulations-hi.md
├── examination_guidelines/
│   ├── DOC-005-end-sem-exam-rules.md
│   ├── DOC-006-revaluation-and-backlog-policy.md
│   ├── DOC-007-malpractice-penalties.md
│   └── DOC-008-exam-guidelines-kn.md
├── attendance/
│   ├── DOC-009-mandatory-attendance-rules.md
│   ├── DOC-010-medical-leave-condonation.md
│   ├── DOC-011-cie-assessment-framework.md
│   └── DOC-012-attendance-rules-hi.md
├── scholarships/
│   ├── DOC-013-merit-scholarship-scheme.md
│   ├── DOC-014-fee-concession-guidelines.md
│   ├── DOC-015-government-scholarship-portal.md
│   └── DOC-016-scholarship-guidelines-te.md
├── hostel/
│   ├── DOC-017-hostel-allotment-rules.md
│   ├── DOC-018-hostel-discipline-curfew.md
│   ├── DOC-019-anti-ragging-policy.md
│   └── DOC-020-hostel-rules-kn.md
└── placements/
    ├── DOC-021-campus-recruitment-policy.md
    ├── DOC-022-internship-guidelines.md
    ├── DOC-023-placement-code-of-conduct.md
    └── DOC-024-placement-policy-hi.md
```

---

## 6. Machine-Readable Corpus Manifest

The single source of truth for the raw corpus is [`data/raw/corpus_manifest.json`](file:///Users/hemanthkumark/College/BIT/AI:Ml/data/raw/corpus_manifest.json).

### Schema Specification:
```json
{
  "document_id": "string (unique format: DOC-XXX)",
  "title": "string (human-readable title)",
  "category": "string (one of the 6 approved categories)",
  "language": "string (ISO 639-1 code: en, hi, kn, te)",
  "file_path": "string (relative path from repository root)",
  "file_type": "string (md, pdf, docx, txt)",
  "file_size_bytes": "integer",
  "sha256_checksum": "string (hexadecimal SHA-256 hash)",
  "source_type": "string (synthetic | public_domain | authorized)",
  "source_reference": "string (provenance statement)",
  "license_or_usage": "string (usage rights statement)",
  "version": "string (semver format e.g. 1.0)",
  "is_active": "boolean (true for active documents)"
}
```

---

## 7. Corpus Validation Automation

Validation is automated via [`scripts/validate_corpus.py`](file:///Users/hemanthkumark/College/BIT/AI:Ml/scripts/validate_corpus.py).

### Automated Check Suite:
1. **Manifest Integrity:** Validates JSON schema, document ID uniqueness, category validity, language code compliance, and source type definitions.
2. **Physical File Verification:** Confirms all referenced file paths exist on disk, match declared extensions, and are non-empty.
3. **Cryptographic Integrity:** Computes SHA-256 checksum for each file on disk and verifies exact equality with manifest metadata, ensuring zero corrupted or duplicated files.
4. **Category Completeness:** Confirms all 6 mandatory categories contain active documents.
5. **PII Heuristic Scan:** Scans content for accidental phone number strings, Aadhaar format patterns, or dummy student credential leaks.

### Execution Results:
```text
======================================================================
  MULTILINGUAL AI DOCUMENT ASSISTANT - CORPUS VALIDATION
======================================================================

[PASS] Manifest JSON structure valid (24 documents found)
[PASS] Document ID uniqueness verified (24/24 unique)
[PASS] File existence and size verified (24/24 files on disk)
[PASS] SHA-256 Checksums verified (24/24 hashes matched)
[PASS] Category coverage verified (6/6 categories populated)
[PASS] Language code compliance verified (en, hi, kn, te)
[PASS] PII safety scan clean (0 potential PII markers detected)

Validation Status: PASS (24/24 documents fully verified)
```
