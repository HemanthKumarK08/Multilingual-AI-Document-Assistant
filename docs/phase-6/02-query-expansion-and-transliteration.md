# Safe Query Expansion and Transliteration Strategy

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Phase:** Phase 6 — Multilingual and Code-Mixed Processing Optimization  
**Module:** `app/services/retrieval/query_expansion.py`  

---

## 1. Overview

In an institutional environment where official policy documents are authored in formal English, queries submitted in Hindi, Kannada, Telugu, or Romanized/code-mixed forms exhibit cross-lingual semantic gaps during vector search and zero overlap during BM25 lexical search.

The `query_expansion.py` module bridges this gap by generating **bounded, deterministic, and traceable query variants** without modifying source evidence or relying on cloud translation APIs.

---

## 2. Institutional Concept Mappings

The expansion system maps domain terminology across six canonical institutional areas:

```text
1. Attendance & Condonation:
   - "attendance" → ["minimum attendance requirement 75%", "attendance condonation threshold 65%"]
   - "उपस्थिति" / "upastithi" / "ಹಾಜರಾತಿ" / "hajarati" / "హాజరు" / "hajaru" → ["attendance", "minimum attendance percentage"]

2. Revaluation & Examinations:
   - "revaluation" → ["revaluation fee per theory course", "photocopy of evaluated answer script"]
   - "पुनर्मूल्यांकन" / "punarmulyankan" / "ಮರುಮೌಲ್ಯಮಾಪನ" / "marumaulyamapana" / "రీవాల్యుయేషన్" → ["revaluation application fee", "photocopy"]

3. Hostels & Resident Regulations:
   - "curfew" → ["hostel night curfew timing resident students", "night curfew"]
   - "caution deposit" → ["refundable caution deposit hostel accommodation"]
   - "ಕರ್ಫ್ಯೂ" / "samaya" / "samayam" → ["hostel curfew timing", "resident rules"]

4. Scholarships & Concessions:
   - "scholarship" → ["institutional merit-cum-means scholarship income limit", "differently abled tuition fee concession"]
   - "छात्रवृत्ति" / "chhatravritti" / "ಸ್ಕಾಲರ್‌ಶಿಪ್" / "ಸ್కాలర్‌షిప్" → ["merit-cum-means scholarship", "income limit"]

5. Placements & Internships:
   - "placement" → ["placement drive registration eligibility criteria", "placement interview absence penalty fine"]
   - "दंड" / "dand" / "ಶಿಕ್ಷೆ" / "shikshe" / "జరిమానా" / "jarimana" → ["penalty fine", "placement fine"]

6. Academics & MCA Degree Credits:
   - "credits" → ["total credits required for MCA degree 88", "maximum duration for degree completion"]
   - "क्रेडिट" / "ಕ್ರೆಡಿಟ್" / "క్రెడిట్స్" → ["MCA degree total credits 88"]
```

---

## 3. Query Variant Generation Contract

When `expand_query(processed_query, max_variants=4)` is invoked:

1. **Variant 1 (Original Query):** Always the exact normalized query string ($w_1 = 1.0, \text{type} = \text{"original"}$).
2. **Variant 2 (Cross-Lingual / Transliteration):** Formed by mapping identified Indic script or Romanized keyword tokens to canonical English institutional keywords ($w_2 = 0.85, \text{type} = \text{"transliteration"} \mid \text{"indic\_translation"}$).
3. **Variant 3 (Domain Synonym Expansion):** Formed from institutional policy synonym definitions ($w_3 = 0.80, \text{type} = \text{"synonym"}$).
4. **Variant 4 (Broad Policy Concept):** Formed from adjacent institutional terms when candidate terms permit ($w_4 = 0.75, \text{type} = \text{"expanded"}$).

---

## 4. Safety and Grounding Invariance

- **No Semantic Drift:** Expansions are restricted to pre-compiled institutional dictionaries and verified domain terms.
- **Strict Evidence Boundary:** Generated variants are used exclusively for candidate discovery in the vector store and BM25 index. They are **never passed into the prompt context as factual evidence**.
- **No Hallucination Risk:** If an expanded variant retrieves irrelevant chunks, the downstream Evidence Gate rejects candidates failing the relevance score threshold ($\ge 0.35$).
