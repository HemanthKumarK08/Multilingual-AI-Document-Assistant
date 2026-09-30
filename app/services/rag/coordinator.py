"""
Simplified Grounded RAG Coordinator (Reference RAG Architecture)

Pipeline:
  1. Retrieval  — hybrid (vector + BM25 + RRF) via RetrievalCoordinator
  2. Evidence check — minimal: at least one chunk returned
  3. Context building — simple numbered source blocks
  4. LLM generation — Gemini → Groq → Mock with explicit multilingual instruction
  5. Return answer + citations

Replaces the multi-stage, multi-gate, multi-guard coordinator.
"""
from __future__ import annotations

import re
import time
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.core.config import settings
from app.core.logging import logger
from app.services.language.resolution import (
    LANGUAGE_NAMES,
    LANGUAGE_UNAVAILABLE_MESSAGES,
    detect_query_language,
    resolve_response_language,
    validate_target_language_script,
)
from app.services.rag.llm_provider import GroqLLMProvider, LLMProvider, get_llm_provider
from app.services.rag.models import ContextPackage, GroundedAnswer, SourceCitation
from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.models import CandidateChunk, RetrievalFilter

# ---------------------------------------------------------------------------
# Language map & regexes
# ---------------------------------------------------------------------------
_LANG_NAMES = LANGUAGE_NAMES
_URL_RE = re.compile(r"https?://[^\s<>\"'()]+|www\.[^\s<>\"'()]+", re.IGNORECASE)
_NUM_RE = re.compile(r"\b\d+(?:\.\d+)?%?\b")

# ---------------------------------------------------------------------------
# Context builder (simple numbered blocks, no complex stitching)
# ---------------------------------------------------------------------------

def _build_context(candidates: List[CandidateChunk]) -> ContextPackage:
    """Build a simple, clearly labelled context from top candidates."""
    selected_chunks: List[CandidateChunk] = []
    sources: List[SourceCitation] = []
    blocks: List[str] = []
    total_chars = 0
    CHAR_LIMIT = 6000

    for idx, cand in enumerate(candidates, start=1):
        snippet = cand.text_content.strip()
        if not snippet:
            continue
        loc = f"Page {cand.page_number}"
        if cand.section_title:
            loc += f" · {cand.section_title}"
        block = f"[Source {idx}] {cand.filename} ({loc})\n{snippet}"
        block_len = len(block)

        if total_chars + block_len > CHAR_LIMIT and selected_chunks:
            break

        selected_chunks.append(cand)
        sources.append(SourceCitation(
            source_id=f"Source {idx}",
            chunk_id=cand.chunk_id,
            doc_id=cand.doc_id,
            filename=cand.filename,
            page_number=cand.page_number,
            section_title=cand.section_title or "",
            source_start_offset=cand.source_start_offset,
            source_end_offset=cand.source_end_offset,
            file_hash_sha256=cand.file_hash_sha256,
        ))
        blocks.append(block)
        total_chars += block_len

    serialized = "\n\n---\n\n".join(blocks)

    return ContextPackage(
        selected_chunks=selected_chunks,
        serialized_context=serialized,
        total_characters=len(serialized),
        truncated=len(candidates) > len(selected_chunks),
        sources=sources,
    )


# ---------------------------------------------------------------------------
# Prompt builder (Strict Multilingual Format per PART 3)
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """You are a multilingual AI document assistant.
Answer the user's question STRICTLY from the provided context documents.

USER REQUEST LANGUAGE:
{user_request_language}

TARGET RESPONSE LANGUAGE:
{target_response_language}

REQUIRED OUTPUT LANGUAGE:
{required_output_language}

RULES:
1. Use ONLY information from the CONTEXT block below.
2. The user question may be in English, Hindi, Kannada, or Telugu. Understand the question in whatever language it is asked, and locate the matching facts from the CONTEXT.
3. If the answer is not in the context, reply exactly: "Information Not Found in the provided documents."
4. CRITICAL LANGUAGE ENFORCEMENT:
   - Your ENTIRE answer MUST be written in {required_output_language}.
   - Do NOT silently answer in English if the target response language is {target_response_language}.
   - Do NOT mix English sentences into an Indic answer unless the source term itself is an official proper noun or technical abbreviation.
   - For Telugu: write entirely in Telugu (Telugu script: U+0C00–U+0C7F).
   - For Hindi: write entirely in Hindi (Devanagari script: U+0900–U+097F).
   - For Kannada: write entirely in Kannada (Kannada script: U+0C80–U+0CFF).
   - For English: write entirely in English.
5. PRESERVATION RULES:
   - Preserve all numbers, percentages, amounts, and dates exactly as stated (e.g. 75%, 2024, Rs. 50,000).
   - Preserve URLs exactly without translating or altering them (e.g. https://...).
   - Preserve official technical names, model names, product names, organization names, abbreviations (e.g. NIRF, CGTMSE, MCA) and document names where appropriate.
6. CITATIONS:
   - Cite sources using [Source N] notation after each relevant statement (e.g. [Source 1]).

CONTEXT:
{context}"""

_PROMPT_TEMPLATE = """{system}

USER QUESTION: {question}

ANSWER:"""


def _build_prompt(query: str, context_text: str, target_language: str, query_language: str = "en") -> str:
    target_name = LANGUAGE_NAMES.get(target_language.lower(), "English")
    query_name = LANGUAGE_NAMES.get(query_language.lower(), "English")
    system = _SYSTEM_PROMPT.format(
        user_request_language=query_name,
        target_response_language=target_name,
        required_output_language=target_name,
        context=context_text,
    )
    return _PROMPT_TEMPLATE.format(system=system, question=query)


# ---------------------------------------------------------------------------
# URL re-attachment (the one genuinely useful guard)
# ---------------------------------------------------------------------------

def _reattach_url_if_needed(answer_text: str, context_text: str,
                             query: str, target_lang: str) -> str:
    """If query asks for a URL/website and answer lacks one, re-attach from context."""
    query_lower = query.lower()
    is_url_q = any(kw in query_lower for kw in [
        "website", "portal", "url", "link", "site", "where to apply",
        "how to apply", "वेबसाइट", "पोर्टल", "ವೆಬ್‌ಸೈಟ್", "ಪೋರ್ಟಲ್",
        "వెబ్‌సైట్", "పోర్టల్",
    ])
    if not is_url_q:
        return answer_text
    if _URL_RE.search(answer_text):
        return answer_text  # already has URL
    context_urls = _URL_RE.findall(context_text)
    if not context_urls:
        return answer_text

    url = context_urls[0]
    suffixes = {
        "hi": f"\n\nआधिकारिक वेबसाइट: {url}",
        "kn": f"\n\nಅಧಿಕೃತ ವೆಬ್‌ಸೈಟ್: {url}",
        "te": f"\n\nఅధికారిక వెబ్‌సైట్: {url}",
    }
    return answer_text.rstrip() + suffixes.get(target_lang, f"\n\nOfficial Website: {url}")


def _build_translation_prompt(source_answer: str, target_lang: str) -> str:
    target_name = LANGUAGE_NAMES.get(target_lang.lower(), "English")
    script_info = {
        "hi": ("Devanagari", "0900–097F"),
        "kn": ("Kannada", "0C80–0CFF"),
        "te": ("Telugu", "0C00–0C7F"),
        "en": ("Latin", "0020–007F"),
    }.get(target_lang.lower(), ("Native", "0900–0D7F"))

    return f"""You are a professional multilingual translator.
Translate the following grounded document assistant answer into {target_name} ({script_info[0]} script).

STRICT RULES:
1. Translate faithfully and accurately into {target_name}.
2. Do NOT add new information. Do NOT omit factual information.
3. Do NOT answer the original question independently.
4. PRESERVE all citations exactly in their original form (e.g. [Source 1], [Source 2]).
5. PRESERVE all numbers (e.g. 75%), percentages, amounts, dates, names, URLs, and technical terms.
6. Write entirely in {target_name} using native {script_info[0]} script (U+{script_info[1]}).
7. Output ONLY the translated answer text.

SOURCE GROUNDED ANSWER:
{source_answer}

TRANSLATED ANSWER ({target_name}):"""


# ---------------------------------------------------------------------------
# RAG Coordinator
# ---------------------------------------------------------------------------

class RAGCoordinator:
    """
    Resilient Grounded Multilingual RAG Coordinator.
    Implements a multi-step recovery cascade:
      Step 1: Direct multilingual generation via Primary LLM (Gemini)
      Step 2: Direct multilingual generation via Secondary LLM (Groq)
      Step 3: Grounded English intermediate generation
      Step 4: Strict translation into requested Indic language
      Step 5: Positive script validation & single retry
      Step 6: Return GroundedAnswer with response_language = requested language
    """

    def __init__(
        self,
        retrieval_coordinator: Optional[RetrievalCoordinator] = None,
        llm_provider: Optional[LLMProvider] = None,
        secondary_llm_provider: Optional[LLMProvider] = None,
    ):
        self.retrieval_coordinator = retrieval_coordinator or RetrievalCoordinator()
        self.llm_provider = llm_provider or get_llm_provider()
        self.secondary_llm_provider = secondary_llm_provider or GroqLLMProvider()

    def answer(
        self,
        query: str,
        language: Optional[str] = None,
        target_language: Optional[str] = None,
        filters: Optional[RetrievalFilter] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_context_chunks: Optional[int] = None,
        min_evidence_score: Optional[float] = None,
    ) -> GroundedAnswer:
        """
        End-to-end grounded RAG:
          retrieve → build context → prompt → resilient LLM cascade → return answer
        """
        start_time = time.perf_counter()
        query_id = str(uuid4())

        # 1. Authoritative response language resolution
        detected_q_lang = detect_query_language(query)
        resp_lang = resolve_response_language(
            explicit_target_language=target_language,
            query=query,
            detected_query_language=language or detected_q_lang,
        )

        # 2. Retrieval (single-pass hybrid)
        try:
            retrieval = self.retrieval_coordinator.retrieve(
                raw_query=query,
                language=detected_q_lang,
                target_language=resp_lang,
                filters=filters,
            )
            candidates = retrieval.candidates
            retrieval_id = retrieval.retrieval_id
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return self._fallback_answer(
                query_id=query_id,
                reason="RETRIEVAL_ERROR",
                resp_lang=resp_lang,
                latency_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        # 3. Minimal evidence check
        if not candidates:
            return self._fallback_answer(
                query_id=query_id,
                reason="NO_EVIDENCE",
                resp_lang=resp_lang,
                latency_ms=(time.perf_counter() - start_time) * 1000.0,
                retrieval_id=retrieval_id,
            )

        # 4. Build context (simple numbered blocks)
        limit = max_context_chunks or settings.RETRIEVAL_MAX_CONTEXT_CHUNKS
        context = _build_context(candidates[:limit])

        if not context.serialized_context.strip():
            return self._fallback_answer(
                query_id=query_id,
                reason="EMPTY_CONTEXT",
                resp_lang=resp_lang,
                latency_ms=(time.perf_counter() - start_time) * 1000.0,
                retrieval_id=retrieval_id,
            )

        # 4b. Lightweight out-of-domain check for non-Indic queries
        q_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", query.lower()))
        sw = {"what", "the", "for", "and", "how", "does", "where", "can", "which", "who", "when", "tell", "about", "today", "now"}
        content_q = q_tokens - sw
        if content_q and not re.search(r"[\u0900-\u0D7F]", query):
            ctx_tokens = set(re.findall(r"\b[a-zA-Z]{3,}\b", context.serialized_context.lower()))
            overlap = content_q & ctx_tokens
            min_required_overlap = 2 if len(content_q) >= 3 else 1
            if len(overlap) < min_required_overlap:
                return self._fallback_answer(
                    query_id=query_id,
                    reason="NO_KEYWORD_MATCH",
                    resp_lang=resp_lang,
                    latency_ms=(time.perf_counter() - start_time) * 1000.0,
                    retrieval_id=retrieval_id,
                )

        # 5. Resilient LLM Generation Cascade
        prompt = _build_prompt(query, context.serialized_context, resp_lang, detected_q_lang)
        actual_provider = type(self.llm_provider).__name__
        generation_path = "direct_primary"
        answer_text = ""
        is_valid_script = False

        # --- STEP 1: Direct generation via primary provider ---
        try:
            raw_primary = self.llm_provider.generate(
                prompt=prompt,
                temperature=settings.LLM_TEMPERATURE,
                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
            )
            if raw_primary and raw_primary.strip():
                clean_primary = raw_primary.strip()
                if validate_target_language_script(clean_primary, resp_lang):
                    answer_text = clean_primary
                    is_valid_script = True
                    generation_path = "direct_primary"
        except Exception as e:
            logger.warning(f"Primary direct generation failed: {e}")

        # --- STEP 2: Direct generation via secondary provider (Groq) ---
        if resp_lang in ("te", "kn", "hi") and not is_valid_script:
            logger.info(f"[CASCADE] Direct generation for '{resp_lang}' attempting secondary provider.")
            try:
                raw_groq = self.secondary_llm_provider.generate(
                    prompt=prompt,
                    temperature=settings.LLM_TEMPERATURE,
                    max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                    timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                )
                if raw_groq and raw_groq.strip():
                    clean_groq = raw_groq.strip()
                    if validate_target_language_script(clean_groq, resp_lang):
                        answer_text = clean_groq
                        is_valid_script = True
                        actual_provider = type(self.secondary_llm_provider).__name__
                        generation_path = "direct_secondary"
            except Exception as e:
                logger.warning(f"Secondary direct generation failed: {e}")

        # --- STEP 3 & 4: Grounded English Intermediate + Translation Fallback ---
        if resp_lang in ("te", "kn", "hi") and not is_valid_script:
            logger.info(
                f"[CASCADE] Direct Indic generation failed for '{resp_lang}'. "
                f"Engaging Grounded English + Translation Cascade."
            )
            
            # Step 3: Generate grounded English intermediate answer from context
            en_prompt = _build_prompt(query, context.serialized_context, "en", detected_q_lang)
            en_answer = ""
            for prov in [self.llm_provider, self.secondary_llm_provider]:
                try:
                    raw_en = prov.generate(
                        prompt=en_prompt,
                        temperature=settings.LLM_TEMPERATURE,
                        max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                    )
                    if raw_en and raw_en.strip() and raw_en.strip() != settings.RAG_FALLBACK_MESSAGE:
                        en_answer = raw_en.strip()
                        break
                except Exception as e:
                    logger.warning(f"English intermediate generation failed on {type(prov).__name__}: {e}")

            # Verify if English answer indicates genuine insufficient evidence
            is_en_fallback = not en_answer or any(ind in en_answer.lower() for ind in [
                settings.RAG_FALLBACK_MESSAGE.lower().rstrip("."),
                "information not found",
                "not found in the provided",
                "not mentioned in the provided",
                "no information",
            ])

            if is_en_fallback:
                logger.info(f"[CASCADE] English intermediate determined answer is INSUFFICIENT_EVIDENCE.")
                return self._fallback_answer(
                    query_id=query_id,
                    reason="INSUFFICIENT_EVIDENCE",
                    resp_lang=resp_lang,
                    latency_ms=(time.perf_counter() - start_time) * 1000.0,
                    retrieval_id=retrieval_id,
                )

            # Step 4: Translate the grounded English answer into requested Indic language
            trans_prompt = _build_translation_prompt(en_answer, resp_lang)
            translated_text = ""
            for trans_prov in [self.llm_provider, self.secondary_llm_provider]:
                try:
                    raw_trans = trans_prov.generate(
                        prompt=trans_prompt,
                        temperature=settings.LLM_TEMPERATURE,
                        max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                        timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                    )
                    if raw_trans and raw_trans.strip():
                        clean_trans = raw_trans.strip()
                        if validate_target_language_script(clean_trans, resp_lang):
                            translated_text = clean_trans
                            actual_provider = type(trans_prov).__name__
                            generation_path = "fallback_translate"
                            break
                        else:
                            # Step 5: Retry once with explicit script reinforcement
                            logger.info(f"[CASCADE] Translation retry once with script reinforcement for {resp_lang}.")
                            retry_prompt = trans_prompt + f"\n\nCRITICAL: You MUST write your translation using {LANGUAGE_NAMES.get(resp_lang)} script ONLY."
                            raw_retry = trans_prov.generate(
                                prompt=retry_prompt,
                                temperature=0.0,
                                max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
                                timeout_seconds=settings.LLM_TIMEOUT_SECONDS,
                            )
                            if raw_retry and validate_target_language_script(raw_retry.strip(), resp_lang):
                                translated_text = raw_retry.strip()
                                actual_provider = type(trans_prov).__name__
                                generation_path = "fallback_translate"
                                break
                except Exception as e:
                    logger.warning(f"Translation failed on {type(trans_prov).__name__}: {e}")

            if translated_text and validate_target_language_script(translated_text, resp_lang):
                answer_text = translated_text
                is_valid_script = True

        # If English was requested:
        if resp_lang == "en" and not is_valid_script and answer_text:
            is_valid_script = True

        # Final check: only if all generation and translation paths failed completely
        if resp_lang in ("te", "kn", "hi") and not is_valid_script:
            logger.error(
                f"[LANGUAGE] Target '{resp_lang}' could not be produced by direct generation or translation cascade."
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return self._fallback_answer(
                query_id=query_id,
                reason="LANGUAGE_UNAVAILABLE",
                resp_lang=resp_lang,
                latency_ms=elapsed_ms,
                retrieval_id=retrieval_id,
            )

        # 6. Handle fallback message from LLM
        lower_ans = answer_text.lower().strip().strip('"').strip("'")
        fallback_indicators = [
            settings.RAG_FALLBACK_MESSAGE.lower().rstrip("."),
            "information not found",
            "not found in the provided",
            "not mentioned in the provided",
            "not available in the provided",
            "no information",
            "जानकारी नहीं मिली",
            "ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ",
            "ಸಮಾಚಾರ ದೊರೆಯಲಿಲ್ಲ",
            "సమాచారం కనుగొనబడలేదు",
            "సమాచారం లేదు",
        ]
        is_fallback = not answer_text or any(ind in lower_ans for ind in fallback_indicators)
        if is_fallback:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.info(
                f"[LANGUAGE] query_language={detected_q_lang} explicit_target={target_language} "
                f"resolved_target={resp_lang} provider={actual_provider} generation_path={generation_path} "
                f"generated_language={resp_lang} validated_language={resp_lang} response_state=INSUFFICIENT_EVIDENCE"
            )
            return self._fallback_answer(
                query_id=query_id,
                reason="INSUFFICIENT_EVIDENCE",
                resp_lang=resp_lang,
                latency_ms=elapsed_ms,
                retrieval_id=retrieval_id,
            )

        # 7. URL re-attachment (if needed)
        answer_text = _reattach_url_if_needed(
            answer_text, context.serialized_context, query, resp_lang
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # 8. Detect hallucinated citations
        valid_sources = {s.source_id for s in context.sources}
        cited_sources = set(re.findall(r"\[(Source \d+)\]", answer_text))
        hallucinated = cited_sources - valid_sources
        warnings = []
        if hallucinated:
            for h in sorted(hallucinated):
                warnings.append(f"Hallucinated citation: {h} not in retrieved context")

        logger.info(
            f"[LANGUAGE] query_language={detected_q_lang} explicit_target={target_language} "
            f"resolved_target={resp_lang} provider={actual_provider} generation_path={generation_path} "
            f"generated_language={resp_lang} validated_language={resp_lang} response_state=GROUNDED"
        )

        return GroundedAnswer(
            query_id=query_id,
            answer_text=answer_text,
            response_language=resp_lang,
            target_language=resp_lang,
            grounded=True,
            fallback_used=False,
            fallback_reason=None,
            generation_path=generation_path,
            retrieval_id=retrieval_id,
            sources=context.sources,
            confidence_label="HIGH" if candidates[0].dense_score and candidates[0].dense_score > 0.7 else "MEDIUM",
            warnings=warnings,
            latency_ms=round(elapsed_ms, 2),
        )

    def _fallback_answer(
        self,
        query_id: str,
        reason: str,
        resp_lang: str,
        latency_ms: float,
        retrieval_id: Optional[str] = None,
    ) -> GroundedAnswer:
        if reason == "LANGUAGE_UNAVAILABLE":
            ans_text = LANGUAGE_UNAVAILABLE_MESSAGES.get(resp_lang, settings.RAG_FALLBACK_MESSAGE)
        else:
            ans_text = settings.RAG_FALLBACK_MESSAGE

        return GroundedAnswer(
            query_id=query_id,
            answer_text=ans_text,
            response_language=resp_lang,
            target_language=resp_lang,
            grounded=False,
            fallback_used=True,
            fallback_reason=reason,
            generation_path="fallback_unavailable",
            retrieval_id=retrieval_id or "",
            sources=[],
            confidence_label="LOW",
            latency_ms=round(latency_ms, 2),
        )

