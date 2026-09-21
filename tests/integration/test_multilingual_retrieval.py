"""
Integration Tests for Multilingual and Code-Mixed Query Retrieval (Phase 6)
"""

import pytest
from app.services.retrieval.coordinator import RetrievalCoordinator


class TestMultilingualRetrievalIntegration:
    """Integration suite validating cross-lingual retrieval against the vector store."""

    @pytest.fixture(scope="class")
    def coordinator(self):
        return RetrievalCoordinator()

    def test_hindi_attendance_query_retrieves_relevant_chunk(self, coordinator):
        query = "सेमेस्टर परीक्षा में बैठने के लिए न्यूनतम उपस्थिति कितनी आवश्यक है?"
        result = coordinator.retrieve(query)
        assert result.candidates
        top_cand = result.candidates[0]
        # Should retrieve attendance document DOC-ATTN-001
        assert "ATTN" in top_cand.doc_id or "attendance" in top_cand.text_content.lower()
        assert result.query_variant_count >= 1

    def test_kannada_curfew_query_retrieves_hostel_doc(self, coordinator):
        query = "ಹಾಸ್ಟೆಲ್ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ವಾರದ ದಿನಗಳಲ್ಲಿ ಕರ್ಫ್ಯೂ ಸಮಯ ಎಷ್ಟು?"
        result = coordinator.retrieve(query)
        assert result.candidates
        top_docs = [c.doc_id for c in result.candidates[:3]]
        assert any("HOST" in d or "COORD" in d for d in top_docs)

    def test_telugu_revaluation_query_retrieves_exam_doc(self, coordinator):
        query = "రీవాల్యుయేషన్ (Revaluation) దరఖాస్తు రుసుము ఎంత?"
        result = coordinator.retrieve(query)
        assert result.candidates
        top_cand = result.candidates[0]
        assert "EXAM" in top_cand.doc_id or "revaluation" in top_cand.text_content.lower()

    def test_romanized_kanglish_query_retrieval(self, coordinator):
        query = "Hostel re-admission ge minimum attendance percentage eshtu beku?"
        result = coordinator.retrieve(query)
        assert result.candidates
        top_cand = result.candidates[0]
        assert "ATTN" in top_cand.doc_id or "HOST" in top_cand.doc_id or "COORD" in top_cand.doc_id or "attendance" in top_cand.text_content.lower() or "hostel" in top_cand.text_content.lower()

    def test_query_expansion_adds_variant_diagnostics(self, coordinator):
        query = "MCA degree total credits required"
        result = coordinator.retrieve(query, enable_query_expansion=True)
        assert result.query_variant_count >= 1
        assert result.query.query_variants
        assert result.query.query_variants[0].variant_type == "original"
