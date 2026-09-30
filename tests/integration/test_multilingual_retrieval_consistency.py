"""
Integration Tests for Multilingual Retrieval Consistency (Issue 1)

Verifies that queries with identical semantic intent across English, Hindi,
Kannada, and Telugu retrieve the same underlying institutional policy documents
and evidence chunks through E5 dense search + BM25 + multi-variant RRF fusion.

Test Matrix:
1. English IntelliExam technology query
2. Hindi IntelliExam technology query
3. Kannada IntelliExam technology query
4. Telugu IntelliExam technology query
5. English attendance query
6. Hindi attendance query
7. Kannada attendance query
8. Telugu attendance query
9. English CGTMSE query
10. Hindi CGTMSE query
11. Kannada CGTMSE query
12. Telugu CGTMSE query
"""

import pytest
from app.services.retrieval.coordinator import RetrievalCoordinator
from app.services.retrieval.multilingual_variants import generate_retrieval_variants

@pytest.fixture(scope="module")
def coordinator():
    return RetrievalCoordinator()

class TestMultilingualRetrievalConsistency:
    """Tests 1-12: Cross-lingual retrieval consistency across EN, HI, KN, TE."""

    # ── IntelliExam Technology Suite (Cases 1-4) ──────────────────────────────

    def test_1_english_intelliexam_technology(self, coordinator):
        q = "What technologies are used in the IntelliExam project?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-INTELLIEXAM-AI-BAC477" in doc_ids
        assert len(res.candidates) >= 1

    def test_2_hindi_intelliexam_technology(self, coordinator):
        q = "इंटेल एग्जाम प्रोजेक्ट में कौन सा टेक्नोलॉजी से किया गया है"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-INTELLIEXAM-AI-BAC477" in doc_ids
        # Verify language detected as Hindi independently
        assert res.query.language == "hi"

    def test_3_kannada_intelliexam_technology(self, coordinator):
        q = "ಇಂಟೆಲಿ ಎಕ್ಸಾಮ್ ಯೋಜನೆಯಲ್ಲಿ ಯಾವ ತಂತ್ರಜ್ಞಾನವನ್ನು ಬಳಸಲಾಗಿದೆ?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-INTELLIEXAM-AI-BAC477" in doc_ids
        assert res.query.language == "kn"

    def test_4_telugu_intelliexam_technology(self, coordinator):
        q = "ఇంటెల్ ఎగ్జామ్ ప్రాజెక్ట్‌లో ఏ సాంకేతికత ఉపయోగించబడింది?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-INTELLIEXAM-AI-BAC477" in doc_ids
        assert res.query.language == "te"

    # ── Attendance Requirement Suite (Cases 5-8) ─────────────────────────────

    def test_5_english_attendance(self, coordinator):
        q = "What is the minimum attendance required?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-ATTN-001" in doc_ids
        assert res.candidates[0].doc_id == "DOC-ATTN-001"

    def test_6_hindi_attendance(self, coordinator):
        q = "परीक्षा में शामिल होने के लिए न्यूनतम उपस्थिति कितनी होनी चाहिए?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-ATTN-001" in doc_ids
        assert res.candidates[0].doc_id == "DOC-ATTN-001"
        assert res.query.language == "hi"

    def test_7_kannada_attendance(self, coordinator):
        q = "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-ATTN-001" in doc_ids
        assert res.candidates[0].doc_id == "DOC-ATTN-001"
        assert res.query.language == "kn"

    def test_8_telugu_attendance(self, coordinator):
        q = "విద్యార్థులకు పరీక్షలకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-ATTN-001" in doc_ids
        assert res.candidates[0].doc_id == "DOC-ATTN-001"
        assert res.query.language == "te"

    # ── CGTMSE Scheme Suite (Cases 9-12) ─────────────────────────────────────

    def test_9_english_cgtmse(self, coordinator):
        q = "What is the maximum credit guarantee under the CGTMSE scheme?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-MSMESCHEMEBOOKLE-3692EB" in doc_ids

    def test_10_hindi_cgtmse(self, coordinator):
        q = "सीजीटीएमएसई योजना के तहत अधिकतम क्रेडिट गारंटी कितनी है?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-MSMESCHEMEBOOKLE-3692EB" in doc_ids
        assert res.query.language == "hi"

    def test_11_kannada_cgtmse(self, coordinator):
        q = "ಸಿಜಿಟಿಎಂಎಸ್ಇ ಯೋಜನೆಯಡಿ ಗರಿಷ್ಠ ಸಾಲ ಖಾತರಿ ಎಷ್ಟು?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-MSMESCHEMEBOOKLE-3692EB" in doc_ids
        assert res.query.language == "kn"

    def test_12_telugu_cgtmse(self, coordinator):
        q = "సిజిటిఎమ్ఎస్ఇ పథకం కింద గరిష్ట క్రెడిట్ గ్యారెంటీ ఎంత?"
        res = coordinator.retrieve(raw_query=q)
        doc_ids = [c.doc_id for c in res.candidates]
        assert "DOC-UP-MSMESCHEMEBOOKLE-3692EB" in doc_ids
        assert res.query.language == "te"


class TestQuestionIsolationAndVariantGeneration:
    """Verifies fresh query isolation and variant constraints."""

    def test_query_isolation_independent_invocations(self, coordinator):
        q1 = "What technologies are used in the IntelliExam project?"
        res1 = coordinator.retrieve(raw_query=q1)

        q2 = "What is the minimum attendance required?"
        res2 = coordinator.retrieve(raw_query=q2)

        # Confirm results are isolated
        assert res1.candidates[0].doc_id != res2.candidates[0].doc_id
        assert "DOC-UP-INTELLIEXAM-AI-BAC477" in [c.doc_id for c in res1.candidates]
        assert "DOC-ATTN-001" in [c.doc_id for c in res2.candidates]

    def test_max_3_variants_enforced(self):
        queries = [
            "What technologies are used in the IntelliExam project?",
            "इंटेल एग्जाम प्रोजेक्ट में कौन सा टेक्नोलॉजी से किया गया है",
            "ಸಿಜಿಟಿಎಂಎಸ್ಇ ಯೋಜನೆಯಡಿ ಗರಿಷ್ಠ ಸಾಲ ಖಾತರಿ ಎಷ್ಟು?",
            "విద్యార్థులకు పరీక్షలకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?",
        ]
        for q in queries:
            v = generate_retrieval_variants(q)
            assert 1 <= len(v) <= 3
            assert q.strip() in v
