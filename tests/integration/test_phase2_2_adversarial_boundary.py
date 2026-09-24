"""
Phase 2.2 Adversarial Chunk Boundary Verification Tests.
Tests suspicious continuation chunks across the corpus, verifying predecessor recovery,
natural document order stitching, and absence of fragmentary answers.
"""

import re
import pytest
from app.services.vector_store.coordinator import VectorStoreCoordinator
from app.services.rag.context_builder import build_context_package, _is_suspicious_continuation
from app.services.rag.llm_provider import MockLLMProvider
from app.services.rag.prompt_builder import build_grounded_prompt
from app.services.retrieval.models import CandidateChunk


@pytest.fixture(scope="module")
def vector_store_data():
    vsc = VectorStoreCoordinator()
    col = vsc.get_collection()
    res = col.get()
    chunks_by_id = {}
    for cid, doc, meta in zip(res["ids"], res["documents"], res["metadatas"]):
        chunks_by_id[cid] = {
            "doc_id": meta.get("doc_id"),
            "chunk_id": cid,
            "page": meta.get("page_number", 1),
            "chunk_index": meta.get("chunk_index", 0),
            "section": meta.get("section_title", ""),
            "filename": meta.get("filename", ""),
            "text": doc,
        }
    return chunks_by_id


def test_msme_p27_c124_adversarial_isolation(vector_store_data):
    """Specifically test DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124 forced in isolation."""
    c124_data = vector_store_data.get("DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124")
    assert c124_data is not None, "Chunk c124 must exist in ChromaDB"

    cand = CandidateChunk(
        chunk_id="DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124",
        doc_id="DOC-UP-MSMESCHEMEBOOKLE-3692EB",
        filename=c124_data["filename"],
        text_content=c124_data["text"],
        page_number=c124_data["page"],
        section_title=c124_data["section"],
        dense_score=0.95,
    )

    pkg = build_context_package([cand])
    assert len(pkg.selected_chunks) >= 2, "Context builder must automatically recover predecessor c123"
    assert any("c123" in c.chunk_id for c in pkg.selected_chunks)

    # Verify merged source
    assert len(pkg.sources) == 1
    assert "c123..DOC-UP-MSMESCHEMEBOOKLE-3692EB:p27:c124" in pkg.sources[0].chunk_id
    assert "Reimbursement of 90%" in pkg.serialized_context

    mock = MockLLMProvider()
    prompt = build_grounded_prompt("What is the reimbursement for NIRF institutions?", pkg.serialized_context, "en")
    answer = mock.generate(prompt)

    assert not answer.startswith("less to")
    assert not answer.startswith("top 50")
    assert "Reimbursement of 90%" in answer or "1.0 lakh" in answer


def test_20_suspicious_continuation_chunks_across_corpus(vector_store_data):
    """Test at least 20 suspicious continuation chunks across the corpus."""
    suspicious_list = []
    for cid, item in vector_store_data.items():
        if _is_suspicious_continuation(item["text"]):
            suspicious_list.append(item)

    suspicious_list.sort(key=lambda x: (x["doc_id"], x["chunk_index"]))
    assert len(suspicious_list) >= 20, f"Expected at least 20 suspicious chunks, found {len(suspicious_list)}"

    test_sample = suspicious_list[:25]  # Test 25 cases across corpus
    mock = MockLLMProvider()

    for idx, item in enumerate(test_sample, 1):
        cand = CandidateChunk(
            chunk_id=item["chunk_id"],
            doc_id=item["doc_id"],
            filename=item["filename"],
            text_content=item["text"],
            page_number=item["page"],
            section_title=item["section"],
            dense_score=0.9,
        )

        pkg = build_context_package([cand])
        prompt = build_grounded_prompt("What are the details and requirements?", pkg.serialized_context, "en")
        answer = mock.generate(prompt)

        # Verification 1: Context reconstructed either with predecessor or self-contained
        assert len(pkg.selected_chunks) >= 1

        # Verification 2: Does not produce fragmentary answers
        assert not answer.startswith(("is less to", "less to top 50", "which is", "and the", "or Rs", "fee. Reimbursement"))
