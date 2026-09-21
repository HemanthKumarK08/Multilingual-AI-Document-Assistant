"""
Unit Tests for Multilingual Processing and Script Analysis (Phase 6)
"""

import pytest
from app.services.retrieval.exceptions import QueryValidationError
from app.services.retrieval.query_processing import (
    compute_script_distribution,
    detect_romanized_language,
    normalize_query_text,
    process_query,
)


class TestMultilingualProcessingUnit:
    """Test suite for Unicode normalization, script distribution, and Romanized classification."""

    def test_normalization_idempotency(self):
        sample = "  ಕಾಲೇಜಿನ   ಹಾಜರಾತಿ   ನಿಯಮಗಳು ??  100%  "
        norm1 = normalize_query_text(sample)
        norm2 = normalize_query_text(norm1)
        assert norm1 == norm2
        assert "  " not in norm1

    def test_unicode_nfc_normalization(self):
        # Decomposed form vs Composed form
        decomposed = "क\u094d\u0937"  # k + virama + ssa
        composed = normalize_query_text(decomposed)
        assert len(composed) > 0

    def test_control_character_removal_preserving_indic(self):
        dirty = "Attendance\x00\x08 Policy\u200C 75% \t \n"
        cleaned = normalize_query_text(dirty)
        assert "\x00" not in cleaned
        assert "\x08" not in cleaned
        assert "Attendance Policy" in cleaned
        assert "75%" in cleaned

    def test_empty_query_raises_validation_error(self):
        with pytest.raises(QueryValidationError):
            normalize_query_text("")
        with pytest.raises(QueryValidationError):
            normalize_query_text("   \n\t  ")

    def test_script_distribution_calculation(self):
        text = "Hello ಹಾಸ್ಟೆಲ್"
        dist = compute_script_distribution(text)
        assert dist["latin"] > 0.0
        assert dist["kannada"] > 0.0
        assert dist["devanagari"] == 0.0
        assert dist["telugu"] == 0.0

    def test_detect_romanized_kannada(self):
        text = "Hostel curfew timing eshtu beku"
        lang, conf = detect_romanized_language(text)
        assert lang == "kn"
        assert conf > 0.0

    def test_detect_romanized_hindi(self):
        text = "Exam fee kitna lagega aur kab apply karein"
        lang, conf = detect_romanized_language(text)
        assert lang == "hi"
        assert conf > 0.0

    def test_detect_romanized_telugu(self):
        text = "Scholarship income limit entha undali"
        lang, conf = detect_romanized_language(text)
        assert lang == "te"
        assert conf > 0.0

    def test_process_query_native_devanagari(self):
        pq = process_query("कक्षा में न्यूनतम उपस्थिति कितनी है?")
        assert pq.script == "Devanagari"
        assert pq.language == "hi"
        assert not pq.is_romanized

    def test_process_query_native_kannada(self):
        pq = process_query("ಹಾಸ್ಟೆಲ್ ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಕರ್ಫ್ಯೂ ಸಮಯ ಎಷ್ಟು?")
        assert pq.script == "Kannada"
        assert pq.language == "kn"
        assert not pq.is_romanized

    def test_process_query_native_telugu(self):
        pq = process_query("రీవాల్యుయేషన్ దరఖాస్తు రుసుము ఎంత?")
        assert pq.script == "Telugu"
        assert pq.language == "te"
        assert not pq.is_romanized

    def test_process_query_code_mixed_indic_latin(self):
        pq = process_query("MCA degree ge minimum attendance eshtu beku?")
        assert pq.is_code_mixed
        assert pq.is_romanized
        assert pq.language == "kn"
