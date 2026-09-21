"""
Unit Tests for Multilingual Query Expansion and Transliteration (Phase 6)
"""

import pytest
from app.services.retrieval.models import ProcessedQuery, QueryVariant
from app.services.retrieval.query_expansion import (
    expand_query,
    extract_matched_expansion_terms,
)


class TestQueryExpansionUnit:
    """Test suite for safe, deterministic query expansion and transliteration."""

    def test_original_query_is_always_first_variant(self):
        pq = ProcessedQuery(
            raw_query="What is the attendance requirement?",
            normalized_query="What is the attendance requirement?",
            language="en",
            script="Latin",
        )
        variants = expand_query(pq, max_variants=4)
        assert len(variants) >= 1
        assert variants[0].variant_type == "original"
        assert variants[0].variant_text == pq.normalized_query
        assert variants[0].weight == 1.0

    def test_hindi_query_expansion_and_transliteration(self):
        pq = ProcessedQuery(
            raw_query="सेमेस्टर परीक्षा में न्यूनतम उपस्थिति कितनी आवश्यक है?",
            normalized_query="सेमेस्टर परीक्षा में न्यूनतम उपस्थिति कितनी आवश्यक है?",
            language="hi",
            script="Devanagari",
        )
        variants = expand_query(pq, max_variants=4)
        assert len(variants) >= 2
        types = [v.variant_type for v in variants]
        assert "indic_translation" in types or "synonym" in types
        # Check that transliteration/translation contains attendance concepts
        variant_texts = " ".join([v.variant_text.lower() for v in variants])
        assert "attendance" in variant_texts

    def test_kannada_query_expansion(self):
        pq = ProcessedQuery(
            raw_query="ಹಾಸ್ಟೆಲ್ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಕರ್ಫ್ಯೂ ಸಮಯ ಎಷ್ಟು?",
            normalized_query="ಹಾಸ್ಟೆಲ್ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಕರ್ಫ್ಯೂ ಸಮಯ ಎಷ್ಟು?",
            language="kn",
            script="Kannada",
        )
        variants = expand_query(pq, max_variants=4)
        assert len(variants) >= 2
        variant_texts = " ".join([v.variant_text.lower() for v in variants])
        assert "curfew" in variant_texts or "hostel" in variant_texts

    def test_telugu_query_expansion(self):
        pq = ProcessedQuery(
            raw_query="రీవాల్యుయేషన్ దరఖాస్తు రుసుము ఎంత?",
            normalized_query="రీవాల్యుయేషన్ దరఖాస్తు రుసుము ఎంత?",
            language="te",
            script="Telugu",
        )
        variants = expand_query(pq, max_variants=4)
        assert len(variants) >= 2
        variant_texts = " ".join([v.variant_text.lower() for v in variants])
        assert "revaluation" in variant_texts or "fee" in variant_texts

    def test_romanized_code_mixed_expansion(self):
        pq = ProcessedQuery(
            raw_query="Hostel re-admission ge minimum attendance percentage eshtu beku?",
            normalized_query="Hostel re-admission ge minimum attendance percentage eshtu beku?",
            language="kn",
            script="Latin",
            is_romanized=True,
            is_code_mixed=True,
        )
        variants = expand_query(pq, max_variants=4)
        assert len(variants) >= 2
        assert variants[0].variant_type == "original"
        variant_texts = " ".join([v.variant_text.lower() for v in variants])
        assert "attendance" in variant_texts

    def test_max_variants_limit_enforced(self):
        pq = ProcessedQuery(
            raw_query="attendance revaluation scholarship hostel placement credits",
            normalized_query="attendance revaluation scholarship hostel placement credits",
            language="en",
            script="Latin",
        )
        variants = expand_query(pq, max_variants=3)
        assert len(variants) <= 3

    def test_disabled_expansion_returns_only_original(self):
        pq = ProcessedQuery(
            raw_query="attendance requirement",
            normalized_query="attendance requirement",
            language="en",
            script="Latin",
        )
        variants = expand_query(pq, max_variants=4, enable_expansion=False)
        assert len(variants) == 1
        assert variants[0].variant_type == "original"

    def test_no_duplicate_variants_generated(self):
        pq = ProcessedQuery(
            raw_query="attendance attendance minimum",
            normalized_query="attendance attendance minimum",
            language="en",
            script="Latin",
        )
        variants = expand_query(pq, max_variants=4)
        texts = [v.variant_text.lower().strip() for v in variants]
        assert len(texts) == len(set(texts))
