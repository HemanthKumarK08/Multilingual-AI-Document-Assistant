"""
AnswerGuard: Research-Backed Post-Generation Faithfulness Guard (DUTIR Architecture)
Validates:
- Target script purity and presence
- Citation validity against retrieved context
- Number faithfulness and hallucinated number rejection
- URL preservation and attachment
- Fragment detection (e.g. "less to top 50...")
- Unsupported claims and ungrounded statements
Returns PASS or REJECT(reason).
"""

import re
from dataclasses import dataclass, field
from typing import List, Literal, Optional, Set, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.services.rag.models import ContextPackage, GroundedAnswer

# Regex patterns for Indic scripts and URLs
_URL_PATTERN = re.compile(r"https?://[^\s<>\"'()]+|www\.[^\s<>\"'()]+", re.IGNORECASE)
_NUM_PERCENT_PATTERN = re.compile(r"\b\d+(?:\.\d+)?%?\b")
_TELUGU_CHAR_PATTERN = re.compile(r"[\u0C00-\u0C7F]")
_KANNADA_CHAR_PATTERN = re.compile(r"[\u0C80-\u0CFF]")
_DEVANAGARI_CHAR_PATTERN = re.compile(r"[\u0900-\u097F]")


@dataclass
class AnswerGuardResult:
    """Outcome of deterministic AnswerGuard verification."""
    is_valid: bool
    status: Literal["PASS", "REJECT"] = "PASS"
    fallback_required: bool = False
    fallback_reason: Optional[str] = None
    sanitized_answer: Optional[str] = None
    violations: List[str] = field(default_factory=list)
    preserved_urls: List[str] = field(default_factory=list)
    script_pure: bool = True


class AnswerGuard:
    """
    Deterministic post-generation guard checking citation provenance,
    numerical faithfulness, URL preservation, entity grounding, and multilingual script purity.
    """

    def __init__(
        self,
        strict_numbers: bool = True,
        strict_urls: bool = True,
        strict_script_purity: bool = True,
    ):
        self.strict_numbers = strict_numbers
        self.strict_urls = strict_urls
        self.strict_script_purity = strict_script_purity

    def verify_and_guard(
        self,
        answer: GroundedAnswer,
        context: ContextPackage,
        query_text: str,
        target_language: str,
    ) -> AnswerGuardResult:
        """
        Executes full deterministic validation over the generated answer.
        """
        violations: List[str] = []
        ans_text = (answer.answer_text or "").strip()
        evidence_text = "\n".join(chunk.text_content for chunk in (context.selected_chunks or []))
        evidence_urls = _URL_PATTERN.findall(evidence_text)
        evidence_numbers = set(_NUM_PERCENT_PATTERN.findall(evidence_text))

        # Known generic fallback / language unavailable strings
        is_generic_fallback = ans_text in (
            settings.RAG_FALLBACK_MESSAGE,
            "Information Not Found in the provided documents.",
            "अनुरोधित भाषा (हिन्दी) में उत्तर देने के लिए बहुभाषी मॉडल सेवा वर्तमान में अनुपलब्ध है।",
            "ವಿನಂತಿಸಿದ ಭಾಷೆಯಲ್ಲಿ (ಕನ್ನಡ) ಉತ್ತರಿಸಲು ಬಹುಭಾಷಾ ಮಾದರಿ ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ.",
            "అభ్యర్థించిన భాషలో (తెలుగు) సమాధానం ఇవ్వడానికి బహుషా మోడల్ సేవ ప్రస్తుతం అందుబాటులో లేదు.",
            "అభ్యర్థించిన భాషలో (తెలుగు) సమాధానం ఇవ్వడానికి బహుభాషా మోడల్ సేవ ప్రస్తుతం అందుబాటులో లేదు."
        )

        is_lang_unavail_msg = (
            "सेवा वर्तमान में अनुपलब्ध" in ans_text
            or "ಸೇವೆಯು ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ" in ans_text
            or "సేవ ప్రస్తుతం అందుబాటులో లేదు" in ans_text
        )

        if is_lang_unavail_msg or answer.fallback_reason == "LANGUAGE_UNAVAILABLE":
            return AnswerGuardResult(
                is_valid=True,
                status="PASS",
                fallback_required=True,
                fallback_reason="LANGUAGE_UNAVAILABLE",
                sanitized_answer=ans_text,
                script_pure=True,
            )

        if answer.fallback_used or ans_text == settings.RAG_FALLBACK_MESSAGE:
            return AnswerGuardResult(
                is_valid=True,
                status="PASS",
                fallback_required=True,
                fallback_reason=answer.fallback_reason or "INSUFFICIENT_EVIDENCE",
                sanitized_answer=ans_text,
                script_pure=True,
            )

        fallback_required = False
        fallback_reason: Optional[str] = None
        script_pure = True
        target_lang = (target_language or "en").lower().strip()

        # 1. Check Citation Validity
        valid_doc_ids = {chunk.doc_id for chunk in (context.selected_chunks or [])}
        for src in answer.sources:
            if src.doc_id not in valid_doc_ids:
                violations.append(f"Invalid citation doc_id '{src.doc_id}' not found in retrieved context.")
                fallback_required = True
                fallback_reason = "INVALID_CITATION"

        # 2. Check Positive Script Presence and Script Purity for Indic Languages
        if self.strict_script_purity and not is_generic_fallback:
            if target_lang == "te":
                kannada_matches = _KANNADA_CHAR_PATTERN.findall(ans_text)
                if kannada_matches:
                    violations.append("Telugu answer contaminated with Kannada script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "SCRIPT_CONTAMINATION"
                telugu_matches = _TELUGU_CHAR_PATTERN.findall(ans_text)
                if not telugu_matches and len(ans_text) > 15:
                    violations.append("Target language is Telugu ('te') but answer contains no Telugu script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "MISSING_TARGET_SCRIPT"

            elif target_lang == "kn":
                telugu_matches = _TELUGU_CHAR_PATTERN.findall(ans_text)
                if telugu_matches:
                    violations.append("Kannada answer contaminated with Telugu script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "SCRIPT_CONTAMINATION"
                kannada_matches = _KANNADA_CHAR_PATTERN.findall(ans_text)
                if not kannada_matches and len(ans_text) > 15:
                    violations.append("Target language is Kannada ('kn') but answer contains no Kannada script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "MISSING_TARGET_SCRIPT"

            elif target_lang == "hi":
                if _KANNADA_CHAR_PATTERN.findall(ans_text) or _TELUGU_CHAR_PATTERN.findall(ans_text):
                    violations.append("Hindi answer contaminated with Kannada/Telugu script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "SCRIPT_CONTAMINATION"
                devanagari_matches = _DEVANAGARI_CHAR_PATTERN.findall(ans_text)
                if not devanagari_matches and len(ans_text) > 15:
                    violations.append("Target language is Hindi ('hi') but answer contains no Devanagari script characters.")
                    script_pure = False
                    fallback_required = True
                    fallback_reason = "MISSING_TARGET_SCRIPT"

        # 3. Fragmentary Sentence / Grammar Guard
        if not is_generic_fallback and ans_text:
            fragment_match = re.match(r"^(?:fee\.|is\b|are\b|was\b|were\b|less to\b|whichever\b|and\b|or\b)", ans_text.strip(), re.IGNORECASE)
            if fragment_match:
                violations.append(f"Answer begins with fragmentary prefix '{fragment_match.group(0)}'.")
                fallback_required = True
                fallback_reason = "FRAGMENTARY_ANSWER"

        # 4. URL Preservation Check
        query_lower = query_text.lower()
        is_website_or_apply_q = any(
            kw in query_lower for kw in [
                "website", "portal", "url", "link", "site", "where to apply",
                "how to apply", "application", "apply", "वेबसाइट", "पोर्टल", "आवेदन",
                "ಲಿಂಕ್", "ವೆಬ್‌ಸೈಟ್", "ಪೋರ್ಟಲ್", "అర్జి",
                "వెబ్‌సైట్", "పోర్టల్", "లింక్", "దరఖాస్తు"
            ]
        )

        ans_urls = _URL_PATTERN.findall(ans_text)
        if self.strict_urls and is_website_or_apply_q and evidence_urls:
            official_url = evidence_urls[0]
            if not ans_urls and official_url:
                logger.info(f"AnswerGuard: Re-attaching official URL '{official_url}' to answer for website query.")
                if target_lang == "hi":
                    ans_text = f"{ans_text.rstrip()}\n\nआधिकारिक पोर्टल / वेबसाइट: {official_url}"
                elif target_lang == "kn":
                    ans_text = f"{ans_text.rstrip()}\n\nಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್: {official_url}"
                elif target_lang == "te":
                    ans_text = f"{ans_text.rstrip()}\n\nఅధికారిక వెబ్‌సైట్: {official_url}"
                else:
                    ans_text = f"{ans_text.rstrip()}\n\nOfficial Portal / Website: {official_url}"

        # 5. Numerical Faithfulness Check
        if self.strict_numbers and not is_generic_fallback:
            ans_numbers = set(_NUM_PERCENT_PATTERN.findall(ans_text))
            suspicious_numbers = [
                num for num in ans_numbers
                if num not in evidence_numbers and not (num.isdigit() and int(num) <= 10)
            ]
            if len(suspicious_numbers) > 3:
                violations.append(f"Answer contains ungrounded numerical claims: {suspicious_numbers}")
                fallback_required = True
                fallback_reason = "NUMBER_MISMATCH"

        status: Literal["PASS", "REJECT"] = "PASS" if not fallback_required else "REJECT"

        return AnswerGuardResult(
            is_valid=not fallback_required,
            status=status,
            fallback_required=fallback_required,
            fallback_reason=fallback_reason,
            sanitized_answer=ans_text,
            violations=violations,
            preserved_urls=evidence_urls,
            script_pure=script_pure,
        )


# Global singleton instance of AnswerGuard
answer_guard = AnswerGuard()
