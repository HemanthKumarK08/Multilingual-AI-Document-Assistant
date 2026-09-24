"""
Query Processing, Multi-Turn Context Resolution, and Intent Understanding Module
Implements research-grounded query understanding (DUTIR/CrossRAG):
- Normalizes Unicode and text idempotently.
- Detects language, script, and Romanized/code-mixed variations.
- Categorizes query intent into 10 distinct semantic classes.
- Extracts entities and important terms.
- Resolves multi-turn conversational dependencies across up to 3 recent turns.
"""

import re
import unicodedata
from typing import Any, Dict, List, Literal, Optional, Tuple

from app.services.ingestion.constants import ScriptType, SupportedLanguage
from app.services.ingestion.language import detect_script_and_language
from app.services.retrieval.exceptions import QueryValidationError
from app.services.retrieval.models import ProcessedQuery

# Indic Unicode ranges
_DEVANAGARI_RANGE = (0x0900, 0x097F)
_KANNADA_RANGE = (0x0C80, 0x0CFF)
_TELUGU_RANGE = (0x0C00, 0x0C7F)

# Romanized functional markers for Indic language detection
_HINDI_ROMANIZED_MARKERS = {
    "kitna", "kitne", "kitni", "kab", "kya", "kaise", "kahan", "hote", "hain",
    "hai", "lagega", "hoga", "karna", "chahiye", "rahega", "par", "mein", "me",
    "ke", "ki", "ko", "se", "nahi", "karo", "diya", "sakta", "sakte", "bhi"
}

_KANNADA_ROMANIZED_MARKERS = {
    "eshtu", "yestu", "enu", "yenu", "beku", "agutte", "aagutte", "ide", "illa",
    "hege", "yelli", "yaavudu", "madabeku", "irabeku", "beka", "ge", "alli",
    "inda", "annu", "na", "matte", "hagadare", "koduva", "thappu"
}

_TELUGU_ROMANIZED_MARKERS = {
    "entha", "yenta", "emiti", "emi", "ela", "undali", "undi", "ledu", "ekkada",
    "chesukovali", "ivvabaduthundi", "untundi", "gurinchi", "kani", "cheyadaniki",
    "vastundi", "chesina", "pedda", "chala"
}

_QUERY_STOPWORDS = {
    "what", "is", "the", "in", "for", "to", "of", "and", "a", "an", "on", "are",
    "how", "do", "does", "did", "explain", "about", "which", "where", "can", "be",
    "who", "whom", "whose", "when", "why", "won", "was", "were", "been", "have", "has",
    "tell", "me", "used", "with", "from", "at", "by", "use", "using", "mentioned",
    "any", "some", "give", "detail", "details", "system", "platform", "please",
    "i", "my", "we", "you", "your", "they", "them", "it", "this", "that"
}

_KNOWN_ENTITIES = {
    "NIRF", "CGTMSE", "MSME", "MCA", "SFURTI", "ASPIRE", "AICTE", "UGC", "VTU",
    "MLI", "MLIS", "FASTAPI", "REACT", "ELECTRON", "MYSQL", "PYSPARK", "CHROMADB",
    "PYTHON", "NODE", "INTELLIEXAM", "NOC", "CGPA", "SGPA", "NBFC", "NBFCS",
    "SIDBI", "MUDRA", "PMEGP", "CLCSS"
}

_OUT_OF_DOMAIN_PATTERNS = [
    r"\bcafeteria\s+menu\b", r"\bmarine\s+biology\b", r"\bcricket\s+coach\b",
    r"\bcookie\s+recipe\b", r"\bpizza\b", r"\bmars\s+mission\b", r"\balien\s+life\b",
    r"\bquantum\s+gravity\b", r"\bmacbook\s+subsidy\b", r"\bbaking\b",
]


def normalize_query_text(raw_query: str) -> str:
    """
    Applies deterministic, idempotent Unicode normalization and cleaning:
    - Normalizes Unicode to standard NFC form.
    - Preserves zero-width joiners where necessary for Indic ligatures.
    - Removes non-printable control characters.
    - Preserves numbers, percentages, URLs, currency symbols, and basic punctuation.
    - Collapses repeated whitespace and strips leading/trailing spaces.
    """
    if raw_query is None:
        raise QueryValidationError("Query cannot be None.")

    # 1. Unicode NFC normalization
    normalized = unicodedata.normalize("NFC", raw_query)

    # 2. Clean non-printable control characters while preserving Indic characters and standard whitespace
    cleaned_chars: List[str] = []
    for ch in normalized:
        cat = unicodedata.category(ch)
        if cat.startswith("C") and ch not in ("\u200C", "\u200D", "\t", "\n", "\r"):
            continue
        cleaned_chars.append(ch)
    normalized = "".join(cleaned_chars)

    # 3. Standardize whitespace
    normalized = re.sub(r"[\r\n\t]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    if not normalized:
        raise QueryValidationError("Query cannot be empty or whitespace-only.")

    return normalized


def compute_script_distribution(text: str) -> Dict[str, float]:
    """
    Computes exact fractional character distribution across recognized scripts.
    """
    counts = {
        "latin": 0,
        "devanagari": 0,
        "kannada": 0,
        "telugu": 0,
        "other": 0,
    }
    total = 0

    for ch in text:
        cp = ord(ch)
        if 0x0041 <= cp <= 0x005A or 0x0061 <= cp <= 0x007A or 0x00C0 <= cp <= 0x017F:
            counts["latin"] += 1
            total += 1
        elif _DEVANAGARI_RANGE[0] <= cp <= _DEVANAGARI_RANGE[1]:
            counts["devanagari"] += 1
            total += 1
        elif _KANNADA_RANGE[0] <= cp <= _KANNADA_RANGE[1]:
            counts["kannada"] += 1
            total += 1
        elif _TELUGU_RANGE[0] <= cp <= _TELUGU_RANGE[1]:
            counts["telugu"] += 1
            total += 1
        elif unicodedata.category(ch).startswith("L"):
            counts["other"] += 1
            total += 1

    if total == 0:
        return {k: 0.0 for k in counts}

    return {k: round(v / total, 4) for k, v in counts.items()}


def detect_romanized_language(text: str) -> Tuple[Optional[str], float]:
    """
    Detects whether a Latin-script query is Romanized Hindi, Kannada, or Telugu based on functional markers.
    Returns (detected_lang, confidence).
    """
    tokens = [t.lower() for t in re.findall(r"[a-zA-Z]+", text)]
    if not tokens:
        return None, 0.0

    token_set = set(tokens)
    hi_matches = len(token_set & _HINDI_ROMANIZED_MARKERS)
    kn_matches = len(token_set & _KANNADA_ROMANIZED_MARKERS)
    te_matches = len(token_set & _TELUGU_ROMANIZED_MARKERS)

    max_matches = max(hi_matches, kn_matches, te_matches)
    if max_matches == 0:
        return None, 0.0

    confidence = min(1.0, max_matches / max(1, len(tokens) * 0.4))

    if hi_matches == max_matches and hi_matches > kn_matches and hi_matches > te_matches:
        return "hi", confidence
    elif kn_matches == max_matches and kn_matches > hi_matches and kn_matches > te_matches:
        return "kn", confidence
    elif te_matches == max_matches and te_matches > hi_matches and te_matches > kn_matches:
        return "te", confidence
    elif kn_matches > 0:
        return "kn", confidence
    elif hi_matches > 0:
        return "hi", confidence
    return "te", confidence


def detect_query_intent(
    query_text: str,
) -> Literal[
    "FACTUAL",
    "DEFINITION",
    "HOW_TO",
    "WHERE_TO",
    "NUMERICAL",
    "POLICY",
    "COMPARISON",
    "LIST",
    "OUT_OF_DOMAIN",
    "AMBIGUOUS",
]:
    """
    Deterministically classifies query intent across 10 structured categories.
    """
    q_lower = query_text.lower().strip()

    # 1. Ambiguous / Empty / Gibberish checks
    alphanumeric_chars = re.findall(r"\w", q_lower)
    if len(alphanumeric_chars) < 3 or re.match(r"^[asdfghjklqwertyuiopzxcvbnm]{4,}$", q_lower):
        if not any(k in q_lower for k in ["fee", "mca", "doc", "lab", "vtu"]):
            return "AMBIGUOUS"

    # 2. Out of Domain
    for pattern in _OUT_OF_DOMAIN_PATTERNS:
        if re.search(pattern, q_lower):
            return "OUT_OF_DOMAIN"

    # 3. Where To / URL / Portal
    if any(
        kw in q_lower
        for kw in [
            "where", "which website", "official website", "portal", "link", "url",
            "where can i", "where to apply", "where should i", "kahan", "yelli", "ekkada",
            "वेबसाइट", "पोर्टल", "ವೆಬ್‌ಸೈಟ್", "ಪೋರ್ಟಲ್", "వెబ్‌సైట్", "పోర్టల్"
        ]
    ):
        return "WHERE_TO"

    # 4. How To / Process / Application
    if any(
        kw in q_lower
        for kw in [
            "how to", "how do i", "how can i", "procedure", "process", "steps",
            "how to apply", "kaise", "hege", "ela", "आवेदन", "ಅರ್ಜಿ", "దరఖాస్తు"
        ]
    ):
        return "HOW_TO"

    # 5. Numerical / Fee / Percentage / Attendance / Credits
    if any(
        kw in q_lower
        for kw in [
            "how much", "how many", "fee", "fees", "cost", "percentage", "percent", "%",
            "minimum attendance", "attendance percentage", "credits", "credit", "cgpa", "sgpa",
            "cutoff", "cut-off", "amount", "rupees", "rs", "₹", "limit", "ceiling", "shortage",
            "stipend", "penalty fine", "fine", "kitna", "eshtu", "entha", "शुल्क", "ಶುಲ್ಕ", "రుసుము",
            "उपस्थिति", "ಹಾಜರಾತಿ", "హాజరు"
        ]
    ) or bool(re.search(r"\b\d+(?:\.\d+)?%?\b", q_lower)):
        return "NUMERICAL"

    # 6. Policy / Regulations / Conduct
    if any(
        kw in q_lower
        for kw in [
            "policy", "rule", "rules", "regulation", "regulations", "guideline", "guidelines",
            "curfew", "malpractice", "debarment", "debarred", "condonation", "conduct",
            "dress code", "attendance requirement", "eligibility criteria", "discipline"
        ]
    ):
        return "POLICY"

    # 7. Comparison
    if any(
        kw in q_lower
        for kw in [
            "difference between", "compare", "versus", "vs", "better", "advantages of", "comparison"
        ]
    ):
        return "COMPARISON"

    # 8. List
    if any(
        kw in q_lower
        for kw in [
            "list of", "all schemes", "what are the", "name the", "types of", "list all"
        ]
    ):
        return "LIST"

    # 9. Definition
    if any(
        kw in q_lower
        for kw in [
            "what is", "define", "definition", "meaning of", "stands for", "full form",
            "kya hai", "enu", "emiti", "अर्थ", "ಅರ್ಥ", "అర్థం"
        ]
    ):
        return "DEFINITION"

    return "FACTUAL"


def extract_entities(raw_query: str) -> List[str]:
    """
    Extracts named entities, acronyms, technical terms, and proper nouns.
    """
    entities: List[str] = []
    seen: set = set()

    # 1. Capitalized/Uppercase acronyms (2-6 letters) e.g. NIRF, CGTMSE, MCA, MSME
    for match in re.findall(r"\b[A-Z0-9_-]{2,10}\b", raw_query):
        upper = match.upper()
        if upper not in seen and upper not in {"AND", "THE", "FOR", "WHAT", "HOW"}:
            entities.append(match)
            seen.add(upper)

    # 2. Known domain acronyms / institutions regardless of case
    lower = raw_query.lower()
    for ent in _KNOWN_ENTITIES:
        ent_lower = ent.lower()
        if re.search(r"\b" + re.escape(ent_lower) + r"\b", lower) and ent not in seen:
            entities.append(ent)
            seen.add(ent)

    # 3. Quoted substrings
    for quoted in re.findall(r'["\']([^"\']{2,40})["\']', raw_query):
        clean_q = quoted.strip()
        if clean_q and clean_q.upper() not in seen:
            entities.append(clean_q)
            seen.add(clean_q.upper())

    return entities


def extract_important_terms(query_text: str) -> List[str]:
    """
    Extracts high-information terms, domain keywords, and numbers from the query.
    """
    tokens = re.findall(r"[\w%₹$]+", query_text.lower())
    important: List[str] = []
    seen: set = set()

    for tok in tokens:
        if tok in _QUERY_STOPWORDS and not (tok.isdigit() or "%" in tok):
            continue
        if len(tok) <= 1 and not (tok.isdigit() or tok in ("%", "₹", "$")):
            continue
        if tok not in seen:
            important.append(tok)
            seen.add(tok)

    return important


def resolve_conversational_query(
    raw_query: str,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """
    DUTIR-inspired lightweight multi-turn context resolution.
    If the current query contains anaphora (it, this, that, them, the requirement, meet it)
    or is an elliptical follow-up ("What happens if I don't meet it?"), resolves the antecedent
    from the last <=3 conversation turns without storing persistent state.
    """
    if not conversation_history:
        return raw_query

    q_lower = raw_query.lower().strip()
    
    # Anaphora / Pronoun / Elliptical markers
    has_anaphora = any(
        re.search(p, q_lower)
        for p in [
            r"\b(it|this|that|them|the same|its|their)\b",
            r"\bmeet\s+it\b",
            r"\bapply\s+for\s+it\b",
            r"\bhow\s+much\s+is\s+it\b",
            r"\bwhat\s+happens\s+if\s+i\s+don'?t\b",
            r"\bwhat\s+if\s+i\s+fail\b",
            r"\bwhat\s+is\s+the\s+fee\b",
            r"\bwhere\s+can\s+i\s+apply\b",
        ]
    )

    if not has_anaphora:
        return raw_query

    # Look back through the last up to 3 turns
    recent_turns = conversation_history[-3:]
    antecedent_topic = ""

    for turn in reversed(recent_turns):
        turn_text = (
            turn.get("content")
            or turn.get("query_text")
            or turn.get("user_query")
            or ""
        ).lower()
        if not turn_text:
            continue

        if "attendance" in turn_text or "उपस्थिति" in turn_text or "ಹಾಜರಾತಿ" in turn_text or "హాజరు" in turn_text:
            antecedent_topic = "attendance requirement"
            break
        elif "cgtmse" in turn_text or "credit guarantee" in turn_text or "गारंटी" in turn_text or "గ్యారెంటీ" in turn_text:
            antecedent_topic = "CGTMSE credit guarantee scheme"
            break
        elif "nirf" in turn_text:
            antecedent_topic = "NIRF rating management"
            break
        elif "revaluation" in turn_text or "photocopy" in turn_text or "पुनर्मूल्यांकन" in turn_text or "ಮರುಮೌಲ್ಯಮಾಪನ" in turn_text:
            antecedent_topic = "revaluation of answer scripts"
            break
        elif "scholarship" in turn_text or "छात्रवृत्ति" in turn_text or "ಸ್ಕಾಲರ್‌ಶಿಪ್" in turn_text:
            antecedent_topic = "scholarship"
            break
        elif "hostel" in turn_text or "curfew" in turn_text:
            antecedent_topic = "hostel"
            break
        elif "placement" in turn_text or "प्लेसमेंट" in turn_text:
            antecedent_topic = "placement registration"
            break

    if not antecedent_topic:
        return raw_query

    # Rewrite query based on antecedent
    if "meet it" in q_lower or "don't meet it" in q_lower or "dont meet it" in q_lower:
        return f"What happens if a student does not meet the {antecedent_topic}?"
    elif q_lower in ("what is the fee?", "how much is the fee?", "what is the fee", "fee?"):
        return f"What is the fee for {antecedent_topic}?"
    elif q_lower in ("where can i apply?", "where to apply?", "how to apply?", "how to apply"):
        return f"How and where to apply for {antecedent_topic}?"
    elif "it" in q_lower.split():
        # Replace 'it' with the antecedent topic
        rewritten = re.sub(r"\bit\b", antecedent_topic, raw_query, flags=re.IGNORECASE)
        return rewritten

    return f"{raw_query} regarding {antecedent_topic}"


def process_query(
    raw_query: str,
    explicit_language: Optional[str] = None,
    target_language: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> ProcessedQuery:
    """
    Comprehensive, deterministic query understanding layer (DUTIR/CrossRAG):
    - Resolves multi-turn conversation context when history is present.
    - Normalizes Unicode text (idempotent NFC).
    - Computes script distributions across Latin, Devanagari, Kannada, and Telugu.
    - Classifies query intent into 10 structured categories.
    - Extracts named entities and important non-stopword terms.
    - Resolves source and target generation languages.
    """
    # 1. Multi-turn resolution
    resolved_query = resolve_conversational_query(raw_query, conversation_history)

    # 2. Unicode normalization
    normalized = normalize_query_text(resolved_query)

    # 3. Compute script distributions
    dist = compute_script_distribution(normalized)

    # 4. Detect primary script
    non_zero_scripts = {k: v for k, v in dist.items() if v > 0.15 and k != "other"}
    if len(non_zero_scripts) > 1:
        primary_script = "Mixed"
    elif dist["devanagari"] > 0.5:
        primary_script = "Devanagari"
    elif dist["kannada"] > 0.5:
        primary_script = "Kannada"
    elif dist["telugu"] > 0.5:
        primary_script = "Telugu"
    elif dist["latin"] > 0.5:
        primary_script = "Latin"
    else:
        primary_script = "Unknown"

    # 5. Detect native script language
    det_result = detect_script_and_language(normalized)
    
    # 6. Check Romanized indicators if Latin or Mixed
    is_romanized = False
    is_code_mixed = False
    detected_romanized_lang, rom_conf = detect_romanized_language(normalized)

    # 7. Determine final detected language code
    if explicit_language and explicit_language.strip() and explicit_language.strip().lower() not in ("auto", "und"):
        lang = explicit_language.strip().lower()
        lang_source = "explicit"
        if primary_script == "Latin" and lang in ["hi", "kn", "te"]:
            is_romanized = True
    else:
        if primary_script == "Devanagari":
            lang = "hi"
            lang_source = "detected"
        elif primary_script == "Kannada":
            lang = "kn"
            lang_source = "detected"
        elif primary_script == "Telugu":
            lang = "te"
            lang_source = "detected"
        elif primary_script in ("Latin", "Mixed"):
            if detected_romanized_lang and rom_conf >= 0.2:
                lang = detected_romanized_lang
                lang_source = "detected"
                is_romanized = True
                is_code_mixed = True
            else:
                lang = "en"
                lang_source = "detected"
        else:
            lang = det_result.language if det_result.language != "und" else "en"
            lang_source = "default"

    # Code-mixed evaluation
    has_latin = dist.get("latin", 0.0) > 0.1
    has_indic = (dist.get("devanagari", 0.0) + dist.get("kannada", 0.0) + dist.get("telugu", 0.0)) > 0.1
    if has_latin and has_indic:
        is_code_mixed = True
    elif is_romanized:
        is_code_mixed = True

    # 8. Query Intent Classification
    intent = detect_query_intent(normalized)

    # 9. Entity and Important Term Extraction
    entities = extract_entities(raw_query)
    important_terms = extract_important_terms(normalized)

    # Resolve target generation language
    resolved_target = (target_language or lang or "en").lower().strip()
    if resolved_target in ("auto", "und"):
        resolved_target = lang if lang != "und" else "en"

    return ProcessedQuery(
        raw_query=raw_query,
        normalized_query=normalized,
        language=lang,
        script=primary_script,
        language_source=lang_source,
        target_language=resolved_target,
        query_intent=intent,
        entities=entities,
        important_terms=important_terms,
        is_code_mixed=bool(is_code_mixed),
        is_romanized=bool(is_romanized),
        is_transliterated=False,
        script_distribution=dist,
    )
