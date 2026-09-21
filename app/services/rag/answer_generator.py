"""
Grounded Answer Generator Module
"""

from typing import Optional, Tuple
from app.core.config import settings
from app.core.logging import logger
from app.services.rag.citation_formatter import resolve_citations
from app.services.rag.exceptions import LLMProviderError
from app.services.rag.llm_provider import LLMProvider, get_llm_provider
from app.services.rag.models import ContextPackage, SourceCitation
from app.services.rag.prompt_builder import build_grounded_prompt


def generate_grounded_answer(
    query_text: str,
    context: ContextPackage,
    target_language: str = "en",
    llm_provider: Optional[LLMProvider] = None,
    temperature: float = 0.0,
    max_output_tokens: int = 512,
    timeout_seconds: int = 60,
) -> Tuple[str, list[SourceCitation], list[str]]:
    """
    Constructs prompt, queries LLM provider, and extracts validated source citations.
    
    Returns:
        Tuple of (raw_answer_text, resolved_citations, warnings).
    """
    provider = llm_provider or get_llm_provider()
    warnings: list[str] = []

    prompt = build_grounded_prompt(
        query_text=query_text,
        context_text=context.serialized_context,
        target_language_code=target_language,
        fallback_message=settings.RAG_FALLBACK_MESSAGE,
    )

    try:
        raw_output = provider.generate(
            prompt=prompt,
            temperature=temperature,
            max_output_tokens=max_output_tokens,
            timeout_seconds=timeout_seconds,
        )
    except Exception as e:
        logger.error(f"LLM generation failed: {str(e)}")
        raise LLMProviderError(f"LLM generation failed: {str(e)}") from e

    cleaned_output = raw_output.strip()

    # Check if model returned fallback message
    if settings.RAG_FALLBACK_MESSAGE.lower() in cleaned_output.lower():
        return settings.RAG_FALLBACK_MESSAGE, [], warnings

    # Resolve citations
    citations, citation_warnings = resolve_citations(cleaned_output, context.sources)
    warnings.extend(citation_warnings)

    return cleaned_output, citations, warnings
