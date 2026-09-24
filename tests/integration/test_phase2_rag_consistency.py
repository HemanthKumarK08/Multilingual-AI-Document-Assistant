"""
Phase 2 RAG Consistency and Multilingual Hardening Verification Tests
Covers sentence-safe chunking, orphan avoidance, contiguous chunk stitching,
positive Indic script validation, attendance vs ballpoint gating, and NIRF complete answers.
"""

import pytest
from app.services.chunking.models import ChunkingConfig
from app.services.chunking.recursive import RecursiveCharacterChunker
from app.services.chunking.validator import ChunkValidator
from app.services.rag.answer_guard import AnswerGuard
from app.services.rag.context_builder import build_context_package
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.evidence_gate import evaluate_evidence_sufficiency
from app.services.rag.llm_provider import MockLLMProvider
from app.services.rag.models import GroundedAnswer
from app.services.retrieval.models import CandidateChunk, ProcessedQuery, RetrievalResult


def test_1_sentence_safe_chunk_overlap():
    """Verify that chunk overlap snaps to sentence/bullet boundaries rather than cutting mid-sentence."""
    text = (
        "Reimbursement of 80% or Rs. 1.0 lakh whichever is less on testing fee.\n\n"
        "• Reimbursement of 90% or course fee or Rs. 1.0 lakh whichever is less to top 50 "
        "NIRF Rated Management Institution’s Short-Term Training Program Fee."
    )
    config = ChunkingConfig(chunk_size=100, chunk_overlap=40, minimum_chunk_size=1)
    chunker = RecursiveCharacterChunker(config=config)
    chunks = chunker.chunk_text(text)

    # Verify no chunk begins with "is less to..."
    for c in chunks:
        assert not c.text.strip().startswith("is less")
        assert not c.text.strip().startswith("less to")


def test_2_no_orphan_chunk_starts():
    """Verify that chunk validation detects orphan words and prevents fragmentary starts."""
    text = "Fee details are provided below.\n\n• First Item is Rs. 100.\n\n• Second Item is Rs. 200."
    config = ChunkingConfig(chunk_size=50, chunk_overlap=15)
    chunker = RecursiveCharacterChunker(config=config)
    chunks = chunker.chunk_text(text)
    for c in chunks:
        assert not c.text.strip().startswith(("is ", "and ", "or ", "less to "))


def test_3_and_4_contiguous_chunk_stitching_and_ordering():
    """Verify that contiguous chunks from the same document and page are stitched into single [Source X]."""
    c1 = CandidateChunk(
        chunk_id="doc1:p27:c124",
        doc_id="doc1",
        filename="msme.pdf",
        page_number=27,
        section_title="Schemes",
        text_content="Reimbursement of 80% on testing fee.",
        rerank_score=0.85,
    )
    c2 = CandidateChunk(
        chunk_id="doc1:p27:c125",
        doc_id="doc1",
        filename="msme.pdf",
        page_number=27,
        section_title="Schemes",
        text_content="Reimbursement of 90% for NIRF short term program fee.",
        rerank_score=0.90,
    )
    # Passed in arbitrary order (c2, c1)
    context = build_context_package([c2, c1])

    # Should produce 1 merged source citation
    assert len(context.sources) == 1
    assert "doc1:p27:c124..doc1:p27:c125" in context.sources[0].chunk_id
    assert "Reimbursement of 80%" in context.serialized_context
    assert "Reimbursement of 90%" in context.serialized_context


def test_5_complete_sentence_fallback_extraction():
    """Verify MockLLMProvider extracts full grammatical sentences, never fragments."""
    prompt = (
        "--- BEGIN CONTEXT EVIDENCE ---\n"
        "[Source 1]\n"
        "Document: msme.pdf\nPage: 27\nSection: Visit:\nChunk ID: doc:p27:c124\n"
        "Content:\n"
        "Reimbursement of 80% or Rs. 1.0 lakh whichever is less on testing fee.\n\n"
        "• Reimbursement of 90% or course fee or Rs. 1.0 lakh whichever is less to top 50 NIRF Rated "
        "Management Institution’s Short-Term Training Program Fee.\n"
        "--- END CONTEXT EVIDENCE ---\n\n"
        "USER QUERY:\nWhat is the reimbursement for top 50 NIRF rated management institutions?\n\n"
        "RESPONSE:"
    )
    provider = MockLLMProvider()
    out = provider.generate(prompt)
    assert "Reimbursement of 90%" in out
    assert "NIRF Rated Management" in out
    assert not out.startswith("less to")
    assert not out.startswith("fee.")


def test_6_telugu_positive_script_validation():
    """Verify AnswerGuard rejects English answers when target language is Telugu."""
    guard = AnswerGuard()
    context = build_context_package([
        CandidateChunk(
            chunk_id="c1", doc_id="d1", filename="f.pdf", page_number=1, text_content="English text content."
        )
    ])
    ans_english = GroundedAnswer(
        query_id="q1",
        answer_text="This is an English answer.",
        response_language="te",
        grounded=True,
        sources=context.sources,
    )
    res = guard.verify_and_guard(ans_english, context, "Query text", "te")
    assert res.is_valid is False
    assert res.fallback_required is True
    assert res.fallback_reason == "MISSING_TARGET_SCRIPT"


def test_7_kannada_positive_script_validation():
    """Verify AnswerGuard rejects English answers when target language is Kannada."""
    guard = AnswerGuard()
    context = build_context_package([
        CandidateChunk(
            chunk_id="c1", doc_id="d1", filename="f.pdf", page_number=1, text_content="English text content."
        )
    ])
    ans_english = GroundedAnswer(
        query_id="q1",
        answer_text="This is an English answer.",
        response_language="kn",
        grounded=True,
        sources=context.sources,
    )
    res = guard.verify_and_guard(ans_english, context, "Query text", "kn")
    assert res.is_valid is False
    assert res.fallback_required is True
    assert res.fallback_reason == "MISSING_TARGET_SCRIPT"


def test_8_hindi_positive_script_validation():
    """Verify AnswerGuard rejects English answers when target language is Hindi."""
    guard = AnswerGuard()
    context = build_context_package([
        CandidateChunk(
            chunk_id="c1", doc_id="d1", filename="f.pdf", page_number=1, text_content="English text content."
        )
    ])
    ans_english = GroundedAnswer(
        query_id="q1",
        answer_text="This is an English answer.",
        response_language="hi",
        grounded=True,
        sources=context.sources,
    )
    res = guard.verify_and_guard(ans_english, context, "Query text", "hi")
    assert res.is_valid is False
    assert res.fallback_required is True
    assert res.fallback_reason == "MISSING_TARGET_SCRIPT"


def test_9_attendance_vs_ballpoint_gating():
    """Verify that an attendance query does NOT accept black ballpoint pen instructions."""
    cand_ballpoint = CandidateChunk(
        chunk_id="c1",
        doc_id="exam_rules",
        filename="instructions.pdf",
        page_number=1,
        section_title="Instructions",
        text_content="Students are required to answer questions using Black ball point pen only.",
        rerank_score=0.80,
    )
    pq = ProcessedQuery(
        raw_query="What is the minimum attendance requirement?",
        normalized_query="What is the minimum attendance requirement?",
        script="latin",
    )
    rr = RetrievalResult(query=pq, candidates=[cand_ballpoint])

    gate_res = evaluate_evidence_sufficiency(rr)
    assert gate_res.is_sufficient is False
    assert gate_res.reason in ("LOW_RELEVANCE", "EMPTY_CONTEXT")


def test_10_nirf_complete_grounded_answer():
    """Verify end-to-end RAG answer for NIRF management fee reimbursement."""
    cand_nirf = CandidateChunk(
        chunk_id="doc1:p27:c124",
        doc_id="doc1",
        filename="msme.pdf",
        page_number=27,
        section_title="Visit:",
        text_content=(
            "• Reimbursement of 90% or course fee or Rs. 1.0 lakh whichever is less to top 50 "
            "NIRF Rated Management Institution’s Short-Term Training Program Fee."
        ),
        rerank_score=0.92,
    )
    rag = RAGCoordinator(llm_provider=MockLLMProvider())
    ans = rag.answer("What is the reimbursement for top 50 NIRF rated management institutions short term training program fee?", language="en")

    assert ans.grounded is True
    assert not ans.answer_text.startswith("less to")
    assert not ans.answer_text.startswith("fee.")
    assert "90%" in ans.answer_text or "1.0 lakh" in ans.answer_text


def test_11_boundary_predecessor_recovery_c124():
    """Verify that when c124 is retrieved alone, predecessor c123 is automatically recovered and stitched."""
    cand_c124 = CandidateChunk(
        chunk_id="DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124",
        doc_id="DOC-UP-MSMESCHEMEBOOKLE-3692EB",
        filename="b9b4423d_MSMESchemebooklet2025-26.pdf",
        page_number=27,
        section_title="Visit:",
        text_content="top 50 NIRF Rated Management Institution’s Short-Term Training Program Fee.\n\nMSME SCHEMES 25\nFor more information and regular updates, visit: www.msme.gov.in",
        dense_score=0.95,
    )
    pkg = build_context_package([cand_c124])

    # Must have recovered predecessor c123
    assert len(pkg.selected_chunks) >= 2
    assert any("c123" in c.chunk_id for c in pkg.selected_chunks)
    assert len(pkg.sources) == 1
    assert "Reimbursement of 90%" in pkg.serialized_context
    assert "www.msme.gov.in" in pkg.serialized_context

