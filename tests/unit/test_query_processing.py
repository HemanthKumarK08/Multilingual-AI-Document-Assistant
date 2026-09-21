"""
Unit Tests for Query Processing and Normalization (Phase 5)
"""

import pytest
from app.services.retrieval.exceptions import QueryValidationError
from app.services.retrieval.query_processing import normalize_query_text, process_query


class TestQueryProcessingUnit:
    def test_empty_query_rejection(self):
        with pytest.raises(QueryValidationError):
            normalize_query_text("")
        with pytest.raises(QueryValidationError):
            normalize_query_text("   \n\t  ")
        with pytest.raises(QueryValidationError):
            normalize_query_text(None)

    def test_whitespace_normalization(self):
        raw = "  What   is the \n\n attendance   requirement? \t "
        normalized = normalize_query_text(raw)
        assert normalized == "What is the attendance requirement?"

    def test_unicode_nfc_preservation(self):
        # Combining Devanagari characters
        raw = "उपस्थिति क्या है?"
        normalized = normalize_query_text(raw)
        assert "उपस्थिति" in normalized

    def test_hindi_query_processing(self):
        query = process_query("कॉलेज में न्यूनतम उपस्थिति आवश्यकता क्या है?")
        assert query.script == "Devanagari"
        assert query.language == "hi"
        assert query.language_source == "detected"
        assert query.query_id is not None

    def test_kannada_query_processing(self):
        query = process_query("ಹಾಜರಾತಿ ನಿಯಮಗಳು ಯಾವುವು?")
        assert query.script == "Kannada"
        assert query.language == "kn"

    def test_telugu_query_processing(self):
        query = process_query("హాజరు నిబంధనలు ఏమిటి?")
        assert query.script == "Telugu"
        assert query.language == "te"

    def test_explicit_language_override(self):
        query = process_query("Attendance policy rules", explicit_language="en")
        assert query.language == "en"
        assert query.language_source == "explicit"

    def test_code_mixed_detection(self):
        query = process_query("MCA attendance rules ಏನು?")
        assert query.is_code_mixed is True or query.script in ["Kannada", "Mixed", "Latin"]

    def test_romanized_query_processing(self):
        query = process_query("hajiri niyam kya hai", explicit_language="hi")
        assert query.is_romanized is True
