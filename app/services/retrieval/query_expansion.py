"""
Safe, Deterministic Multilingual Query Expansion and Transliteration Service (Phase 6)
Generates controlled, traceable query variants for cross-lingual dense and lexical retrieval.
"""

import re
from typing import Dict, List, Set, Tuple

from app.core.config import settings
from app.services.retrieval.models import ProcessedQuery, QueryVariant

# ------------------------------------------------------------------------------
# 1. Cross-Lingual Concept & Keyword Translation Dictionary
# Maps Indic script tokens and Romanized terms into canonical English search terms.
# ------------------------------------------------------------------------------
_INDIC_TERM_TRANSLATIONS: Dict[str, List[str]] = {
    # Attendance & Condonation
    "उपस्थिति": ["attendance", "minimum attendance requirement", "75%"],
    "हाजिरी": ["attendance", "attendance percentage"],
    "कंडोनेशन": ["medical condonation", "attendance shortage condonation 65%"],
    "ಹಾಜರಾತಿ": ["attendance", "minimum attendance requirement", "75%"],
    "ವಿನಾಯಿತಿ": ["condonation", "medical attendance condonation"],
    "ಹಾಜರು": ["attendance", "minimum attendance percentage", "75%"],
    "మినహాయింపు": ["condonation", "attendance condonation 65%"],
    "upastithi": ["attendance", "minimum attendance percentage"],
    "hajarati": ["attendance", "minimum attendance requirement"],
    "hajaru": ["attendance", "minimum attendance threshold"],

    # Revaluation & Examinations
    "पुनर्मूल्यांकन": ["revaluation fee", "photocopy of answer script", "re-evaluation"],
    "शुल्क": ["fee", "charge", "cost"],
    "मруಮೌಲ್ಯಮಾಪನ": ["revaluation fee", "answer script photocopy"],
    "ಮರುಮೌಲ್ಯಮಾಪನ": ["revaluation fee", "answer script photocopy"],
    "ಶುಲ್ಕ": ["fee", "cost", "application fee"],
    "రీవాల్యుయేషన్": ["revaluation application fee", "photocopy cost"],
    "రుసుము": ["fee", "charge", "application fee"],
    "punarmulyankan": ["revaluation fee", "answer script revaluation"],
    "marumaulyamapana": ["revaluation fee", "answer script photocopy"],
    "shulk": ["fee", "revaluation fee"],
    "shulka": ["fee", "revaluation fee"],
    "rusumu": ["fee", "revaluation fee"],

    # Hostel & Rules
    "हॉस्टल": ["hostel", "resident students", "hostel accommodation"],
    "कर्फ्यू": ["hostel curfew timing", "night curfew"],
    "काशन": ["caution deposit", "refundable deposit"],
    "सुरक्षा": ["caution deposit", "security deposit"],
    "ಹಾಸ್ಟೆಲ್": ["hostel accommodation", "resident students"],
    "ಕರ್ಫ್ಯೂ": ["hostel curfew timing", "night curfew"],
    "ಕಾಷನ್": ["caution deposit", "refundable deposit"],
    "ಡೆಪಾಸಿಟ್": ["caution deposit", "deposit"],
    "హాస్టల్": ["hostel accommodation", "resident students"],
    "కర్ఫ్యూ": ["hostel night curfew time"],
    "డిపాజిట్": ["caution deposit", "deposit"],
    "curfew": ["hostel curfew timing", "night curfew"],
    "samay": ["timing", "curfew timing"],
    "samaya": ["timing", "curfew timing"],
    "samayam": ["time", "curfew timing"],

    # Scholarships & Concessions
    "छात्रवृत्ति": ["scholarship", "merit-cum-means scholarship", "income limit"],
    "आय": ["household income limit", "annual income"],
    "दिव्यांग": ["differently abled fee concession", "disability concession"],
    "छूट": ["fee concession", "tuition fee waiver"],
    "ಸ್ಕಾಲರ್‌ಶಿಪ್": ["scholarship", "merit-cum-means scholarship", "income limit"],
    "ಆದಾಯ": ["annual household income limit", "income ceiling"],
    "ವಿಕಲಚೇತನ": ["differently abled student tuition fee concession"],
    "ರಿಯಾಯಿತಿ": ["fee concession", "tuition fee waiver"],
    "స్కాలర్‌షిప్": ["scholarship", "merit-cum-means scholarship", "income limit"],
    "ఆదాయ": ["family annual income limit", "income criteria"],
    "దివ్యాంగ": ["differently abled students tuition fee concession"],
    "రాయితీ": ["fee concession", "tuition fee waiver"],
    "chhatravritti": ["scholarship", "merit-cum-means scholarship"],
    "vikalachethana": ["differently abled tuition fee concession"],
    "divyanga": ["differently abled tuition fee concession"],

    # Placements & Internships
    "प्लेसमेंट": ["placement registration eligibility", "campus drive"],
    "अनुपस्थित": ["placement absence penalty", "placement fine"],
    "दंड": ["penalty fine", "placement fine"],
    "ಪ್ಲೇಸ್‌ಮೆಂಟ್": ["placement registration eligibility", "placement drive"],
    "ಗೈರುಹಾಜರಾದರೆ": ["placement absence penalty fine", "absent penalty"],
    "ಶಿಕ್ಷೆ": ["penalty fine", "placement disciplinary action"],
    "ప్లేస్‌మెంట్": ["placement registration eligibility", "campus drive"],
    "హాజరుకాకపోతే": ["placement absence fine penalty"],
    "జరిమానా": ["penalty fine", "placement fine"],
    "placement": ["placement registration eligibility", "training attendance"],
    "dand": ["penalty fine", "placement fine"],
    "shikshe": ["penalty fine", "placement absence fine"],
    "jarimana": ["penalty fine", "placement fine"],

    # Academics & MCA Credits
    "क्रेडिट": ["MCA degree total credits", "88 credits"],
    "डिग्री": ["degree award credits", "MCA program"],
    "ಕ್ರೆಡಿಟ್": ["MCA degree total credits", "88 credits"],
    "ಪದವಿ": ["MCA degree program credits"],
    "క్రెడిట్స్": ["MCA degree total credits", "88 credits"],
    "డిగ్రీ": ["MCA degree requirements"],
    "credits": ["total credits required MCA degree 88"],
    "mca": ["MCA degree total credits 88", "program duration"],

# Government & MSME Schemes (CGTMSE / Credit Guarantee)
    "क्रेडिट गारंटी": ["credit guarantee scheme cgtmse", "https://www.cgtmse.in", "how to apply MLIs banks"],
    "गारंटी": ["credit guarantee scheme", "cgtmse", "guarantee coverage"],
    "योजना": ["scheme", "government scheme", "cgtmse"],
    "वेबसाइट": ["website", "official portal", "https://www.cgtmse.in", "www.msme.gov.in"],
    "आवेदन": ["how to apply", "application through MLIs banks", "apply online portal"],
    "ಕ್ರೆಡಿಟ್ ಗ್ಯಾರಂಟಿ": ["credit guarantee scheme cgtmse", "https://www.cgtmse.in", "how to apply MLIs banks"],
    "ಗ್ಯಾರಂಟಿ": ["credit guarantee scheme", "cgtmse", "guarantee"],
    "ಯೋಜನೆ": ["scheme", "government scheme"],
    "ವೆಬ್‌ಸೈಟ್": ["website", "official portal", "https://www.cgtmse.in"],
    "ಅರ್ಜಿ": ["how to apply", "application through MLIs banks", "apply online"],
    "క్రెడిట్ గ్యారెంటీ": ["credit guarantee scheme cgtmse", "https://www.cgtmse.in", "how to apply MLIs banks"],
    "గ్యారెంటీ": ["credit guarantee scheme", "cgtmse", "guarantee"],
    "స్కీమ్": ["scheme", "government scheme"],
    "వెబ్‌సైట్": ["website", "official portal", "https://www.cgtmse.in"],
    "దరఖాస్తు": ["how to apply", "application through MLIs banks", "apply online"],
    "cgtmse": ["credit guarantee scheme for micro and small enterprises", "https://www.cgtmse.in", "how to apply MLIs banks"],

    # Anti-Ragging & Emergency
    "एंटी-रैगिंग": ["anti-ragging toll-free emergency helpline number"],
    "हेल्पलाइन": ["emergency toll-free helpline number 24x7"],
    "ಆಂಟಿ-ರ್ಯಾಗಿಂಗ್": ["anti-ragging toll-free emergency helpline"],
    "ರ್ಯಾಗಿಂಗ್": ["anti-ragging 24x7 emergency helpline"],
    "ಸಹಾಯವಾಣಿ": ["emergency toll-free helpline number"],
    "ర్యాగింగ్": ["anti-ragging toll-free emergency helpline number"],
    "హెల్ప్‌లైన్": ["emergency toll-free helpline number"],
    "helpline": ["anti-ragging 24x7 toll-free emergency helpline"],
}

# ------------------------------------------------------------------------------
# 2. English Domain Synonym Expansion Dictionary
# ------------------------------------------------------------------------------
_DOMAIN_SYNONYM_MAPPINGS: Dict[str, List[str]] = {
    "attendance": [
        "minimum attendance requirement 75%",
        "attendance condonation threshold 65%",
        "mandatory attendance policy",
    ],
    "revaluation": [
        "revaluation fee per theory course",
        "photocopy of evaluated answer script",
        "answer script re-evaluation",
    ],
    "hostel": [
        "hostel night curfew timing resident students",
        "refundable caution deposit hostel accommodation",
        "prohibited electric appliances hostel rooms",
    ],
    "scholarship": [
        "institutional merit-cum-means scholarship income limit",
        "differently abled tuition fee concession",
        "national games sports fee waiver gold medalist",
    ],
    "placement": [
        "placement drive registration eligibility criteria",
        "placement interview absence penalty fine",
        "pre-placement training mandatory attendance",
        "dream company interview condition",
    ],
    "credits": [
        "total credits required for MCA degree 88",
        "maximum duration for degree completion",
        "first class with distinction CGPA",
    ],
    "internship": [
        "full-semester industry internship NOC minimum CGPA",
        "internship eligibility prerequisite coursework",
    ],
"cgtmse": [
        "credit guarantee scheme for micro and small enterprises",
        "how to apply through MLIs banks and NBFCs",
        "official guidelines website https://www.cgtmse.in",
    ],
    "guarantee": [
        "credit guarantee scheme for micro and small enterprises cgtmse",
        "collateral free loan up to 5 crore MLIs",
        "detailed guidelines website https://www.cgtmse.in",
    ],
    "website": [
        "official website portal https://www.cgtmse.in",
        "detailed guidelines visit website",
        "how to apply online portal",
    ],
    "ragging": [
        "24x7 toll-free emergency anti-ragging helpline number",
        "anti-ragging committee grievance",
    ],
}


def extract_matched_expansion_terms(query_text: str) -> List[Tuple[str, List[str]]]:
    """
    Extracts matched Indic tokens and domain concepts from the query.
    Returns list of (matched_token, expansion_terms).
    """
    matched: List[Tuple[str, List[str]]] = []
    lower_text = query_text.lower()
    matched_indic_keys: List[str] = []

    # Financial / scheme indicator check to avoid collision with academic course credits
    is_financial_or_scheme = any(
        w in lower_text for w in [
            "गारंटी", "ग್ಯಾರಂಟಿ", "గ్యారెంటీ", "guarantee", "cgtmse", "योजना", "ಯೋಜನೆ", "స్కీమ్", "scheme", "msme"
        ]
    )

    # 1. Match Indic / Romanized translation keywords (longest keys checked first)
    for key, terms in sorted(_INDIC_TERM_TRANSLATIONS.items(), key=lambda x: len(x[0]), reverse=True):
        if key in lower_text or re.search(r"\b" + re.escape(key) + r"\b", lower_text, re.IGNORECASE):
            # Avoid matching shorter substring if longer key was already matched
            if any(key in mk for mk in matched_indic_keys):
                continue
            # If financial guarantee query, do not inject MCA academic degree credits
            if is_financial_or_scheme and key in ["क्रेडिट", "ಕ್ರೆಡಿಟ್", "క్రెడిట్స్", "credits"]:
                continue
            matched.append((key, terms))
            matched_indic_keys.append(key)

    # 2. Match English domain synonyms (longest keys checked first)
    for key, terms in sorted(_DOMAIN_SYNONYM_MAPPINGS.items(), key=lambda x: len(x[0]), reverse=True):
        if re.search(r"\b" + re.escape(key) + r"\b", lower_text, re.IGNORECASE):
            if is_financial_or_scheme and key == "credits":
                continue
            matched.append((key, terms))

    return matched


def expand_query(
    processed_query: ProcessedQuery,
    max_variants: int = 4,
    enable_expansion: bool = True,
    enable_transliteration: bool = True,
) -> List[QueryVariant]:
    """
    Generates bounded, traceable query variants for retrieval:
    1. Variant 1: Original normalized query (Weight = 1.0, Type = 'original').
    2. Variant 2: Transliterated / Cross-lingual English search phrase (Weight = 0.85).
    3. Variant 3: Domain synonym expansion (Weight = 0.80).
    4. Variant 4: Broad policy concept expansion (Weight = 0.75).
    """
    variants: List[QueryVariant] = []

    # Variant 1 is always the original query
    variants.append(QueryVariant(
        variant_text=processed_query.normalized_query,
        variant_type="original",
        weight=1.0,
        language=processed_query.language,
        source_terms=[processed_query.normalized_query],
    ))

    if not enable_expansion:
        return variants

    matched_pairs = extract_matched_expansion_terms(processed_query.normalized_query)
    if not matched_pairs:
        return variants

    # Collect unique candidate expansion phrases
    collected_terms: List[str] = []
    seen_phrases: Set[str] = {processed_query.normalized_query.lower()}
    matched_sources: List[str] = []

    for key, terms in matched_pairs:
        matched_sources.append(key)
        for term in terms:
            if term.lower() not in seen_phrases:
                seen_phrases.add(term.lower())
                collected_terms.append(term)

    limit_terms = settings.RETRIEVAL_MAX_EXPANSION_TERMS

    # Generate cross-lingual translation variant (Variant 2)
    if enable_transliteration and (processed_query.language in ("hi", "kn", "te") or processed_query.is_romanized or processed_query.is_code_mixed):
        if collected_terms:
            cross_lingual_text = " ".join(collected_terms[:3])
            variants.append(QueryVariant(
                variant_text=cross_lingual_text,
                variant_type="transliteration" if processed_query.is_romanized else "indic_translation",
                weight=settings.RETRIEVAL_VARIANT_WEIGHT,
                language="en",
                source_terms=matched_sources[:4],
            ))

    # Generate domain synonym variant (Variant 3)
    if len(variants) < max_variants and len(collected_terms) >= 1:
        synonym_text = collected_terms[0]
        if len(collected_terms) > 1:
            synonym_text = f"{collected_terms[0]} {collected_terms[1]}"
        
        # Check if already added
        if not any(v.variant_text.lower() == synonym_text.lower() for v in variants):
            variants.append(QueryVariant(
                variant_text=synonym_text,
                variant_type="synonym",
                weight=0.80,
                language="en",
                source_terms=matched_sources[:3],
            ))

    # Generate broader expanded variant if space permits (Variant 4)
    if len(variants) < max_variants and len(collected_terms) >= 3:
        expanded_text = " ".join(collected_terms[1:4])
        if not any(v.variant_text.lower() == expanded_text.lower() for v in variants):
            variants.append(QueryVariant(
                variant_text=expanded_text,
                variant_type="expanded",
                weight=0.75,
                language="en",
                source_terms=matched_sources[:4],
            ))

    return variants[:max_variants]
