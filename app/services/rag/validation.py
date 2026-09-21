"""
Answer Grounding and Provenance Validation Module
"""

from typing import List, Tuple
from app.services.rag.models import ContextPackage, GroundedAnswer, SourceCitation

def validate_grounded_answer(
    answer: GroundedAnswer,
    context: ContextPackage,
) -> Tuple[bool, List[str]]:
    """
    Validates that the generated answer respects grounding constraints and citation integrity.
    """
    errors: List[str] = []

    # If fallback was used, verify no citations were fabricated
    if answer.fallback_used:
        if answer.sources:
            errors.append("Fallback answer must not contain fabricated source citations.")
        return len(errors) == 0, errors

    # Check non-empty answer text
    if not answer.answer_text or not answer.answer_text.strip():
        errors.append("Answer text cannot be empty.")

    # Check that cited sources were actually supplied in context
    context_chunk_ids = {s.chunk_id for s in context.sources}
    for src in answer.sources:
        if src.chunk_id not in context_chunk_ids:
            errors.append(f"Answer cited chunk [{src.chunk_id}] which was not in context package.")
        if src.page_number < 1:
            errors.append(f"Answer cited source has invalid page number {src.page_number}.")
        if not src.filename:
            errors.append("Answer cited source missing filename.")

    is_valid = len(errors) == 0
    return is_valid, errors
