#!/usr/bin/env python3
"""
Corpus Validation Script
Performs integrity, checksum, structure, provenance, and privacy checks
across data/raw/corpus_manifest.json and raw document files.
"""

import sys
import json
import hashlib
import re
from pathlib import Path

# Color codes
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

REQUIRED_FIELDS = [
    "document_id",
    "title",
    "category",
    "language",
    "file_path",
    "source_type",
    "checksum_sha256",
    "is_active",
]

ALLOWED_CATEGORIES = {
    "academic_regulations",
    "examination_guidelines",
    "attendance",
    "scholarships",
    "hostel",
    "placements",
}

ALLOWED_LANGUAGES = {"en", "hi", "kn", "te"}
ALLOWED_EXTENSIONS = {".txt", ".pdf", ".docx"}

# Heuristic patterns for accidental personal data leaks
PII_PATTERNS = [
    (r"\b\d{12}\b", "Potential 12-digit Aadhaar number"),
    (r"\b[A-Za-z0-9._%+-]+@(?!institution\.edu)[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "Personal email address"),
]

def main() -> int:
    project_root = Path(__file__).resolve().parent.parent
    manifest_path = project_root / "data" / "raw" / "corpus_manifest.json"

    print("=" * 70)
    print(" MULTILINGUAL AI DOCUMENT ASSISTANT — CORPUS VALIDATION AUDIT")
    print("=" * 70)
    print(f"Manifest Path: {manifest_path}")
    print("-" * 70)

    if not manifest_path.exists():
        print(f"{RED}[FAIL]{RESET} Manifest file missing at {manifest_path}")
        return 1

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            docs = json.load(f)
    except Exception as e:
        print(f"{RED}[FAIL]{RESET} Manifest JSON parsing error: {e}")
        return 1

    if not isinstance(docs, list) or len(docs) == 0:
        print(f"{RED}[FAIL]{RESET} Manifest must be a non-empty JSON list of documents.")
        return 1

    errors = 0
    warnings = 0

    doc_ids_seen = set()
    checksums_seen = set()
    categories_found = set()
    languages_found = set()

    print(f"[1] Validating {len(docs)} documents against schema and integrity rules...\n")

    for idx, doc in enumerate(docs, 1):
        doc_id = doc.get("document_id", f"UNKNOWN_INDEX_{idx}")
        title = doc.get("title", "No Title")

        # 1. Required Fields Check
        missing_fields = [f for f in REQUIRED_FIELDS if f not in doc]
        if missing_fields:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Missing required fields: {missing_fields}")
            errors += 1
            continue

        # 2. Duplicate Document ID Check
        if doc_id in doc_ids_seen:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Duplicate document_id detected!")
            errors += 1
        doc_ids_seen.add(doc_id)

        # 3. Category Validation
        category = doc["category"]
        if category not in ALLOWED_CATEGORIES:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Invalid category '{category}'. Allowed: {ALLOWED_CATEGORIES}")
            errors += 1
        categories_found.add(category)

        # 4. Language Validation
        lang = doc["language"]
        if lang not in ALLOWED_LANGUAGES:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Invalid language code '{lang}'. Allowed: {ALLOWED_LANGUAGES}")
            errors += 1
        languages_found.add(lang)

        # 5. File Existence & Extension Check
        rel_path = doc["file_path"]
        abs_path = project_root / rel_path
        if not abs_path.exists():
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Target file not found at: {rel_path}")
            errors += 1
            continue

        ext = abs_path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Unsupported file extension '{ext}'")
            errors += 1

        # 6. Checksum Verification
        file_bytes = abs_path.read_bytes()
        actual_sha256 = hashlib.sha256(file_bytes).hexdigest()
        expected_sha256 = doc["checksum_sha256"]

        if actual_sha256 != expected_sha256:
            print(f"  {RED}[FAIL]{RESET} [{doc_id}] Checksum mismatch! Manifest: {expected_sha256[:12]}..., Actual: {actual_sha256[:12]}...")
            errors += 1
        elif actual_sha256 in checksums_seen:
            print(f"  {YELLOW}[WARN]{RESET} [{doc_id}] Duplicate file content checksum detected: {actual_sha256[:12]}...")
            warnings += 1
        checksums_seen.add(actual_sha256)

        # 7. Privacy & PII Inspection (for text files)
        if ext in (".txt", ".md"):
            try:
                content = abs_path.read_text(encoding="utf-8")
                for pattern, desc in PII_PATTERNS:
                    if re.search(pattern, content):
                        print(f"  {YELLOW}[WARN]{RESET} [{doc_id}] {desc} detected in text.")
                        warnings += 1
            except Exception as e:
                print(f"  {YELLOW}[WARN]{RESET} [{doc_id}] Text read error during PII check: {e}")

        print(f"  {GREEN}[PASS]{RESET} {doc_id} | {title[:45]:<45} | {category:<22} | {len(file_bytes):>6} B")

    print("\n[2] CORPUS COVERAGE SUMMARY")
    print(f"  Total Documents Ingested : {len(docs)}")
    print(f"  Unique Categories Covered: {len(categories_found)} / {len(ALLOWED_CATEGORIES)}")
    print(f"  Categories Present       : {sorted(list(categories_found))}")
    print(f"  Languages Represented    : {sorted(list(languages_found))}")

    missing_cats = ALLOWED_CATEGORIES - categories_found
    if missing_cats:
        print(f"  {YELLOW}[WARN]{RESET} Missing categories: {missing_cats}")
        warnings += 1

    print("\n" + "=" * 70)
    if errors == 0:
        print(f"{GREEN}CORPUS VALIDATION PASSED:{RESET} All {len(docs)} documents are verified.")
        if warnings > 0:
            print(f"{YELLOW}Note:{RESET} {warnings} non-critical warning(s) observed.")
        print("=" * 70)
        return 0
    else:
        print(f"{RED}CORPUS VALIDATION FAILED:{RESET} {errors} error(s) detected.")
        print("=" * 70)
        return 1

if __name__ == "__main__":
    sys.exit(main())
