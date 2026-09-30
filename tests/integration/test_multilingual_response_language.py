"""
Integration Tests for Multilingual Response Language Resolution & Validation
Covers requirements 1-11 & 20-22 from PART 21:
  - Telugu / Hindi / Kannada / English target propagation
  - English query → Telugu / Hindi / Kannada response
  - Telugu query → English response
  - Positive script validation (English rejected as Telugu/Hindi/Kannada)
  - Zero citations for LANGUAGE_UNAVAILABLE and INSUFFICIENT_EVIDENCE
  - Grounded multilingual answer retains valid citations
"""
import pytest
from app.services.language.resolution import (
    resolve_response_language,
    detect_query_language,
    validate_target_language_script,
    TTS_LOCALE_MAP,
    LANGUAGE_UNAVAILABLE_MESSAGES,
)
from app.services.rag.coordinator import RAGCoordinator
from app.services.rag.llm_provider import MockLLMProvider
from app.services.rag.models import GroundedAnswer, SourceCitation
from app.schemas import QueryResponse, Citation


class TestMultilingualResponseLanguageResolution:
    """Tests 1-8: Authoritative Response Language Resolution & Propagation."""

    def test_telugu_target_propagation(self):
        """1. Telugu target propagation when explicitly requested."""
        resolved = resolve_response_language(
            explicit_target_language="te",
            query="What is the attendance policy?",
            detected_query_language="en",
        )
        assert resolved == "te"

    def test_hindi_target_propagation(self):
        """2. Hindi target propagation when explicitly requested."""
        resolved = resolve_response_language(
            explicit_target_language="hi",
            query="What is the attendance policy?",
            detected_query_language="en",
        )
        assert resolved == "hi"

    def test_kannada_target_propagation(self):
        """3. Kannada target propagation when explicitly requested."""
        resolved = resolve_response_language(
            explicit_target_language="kn",
            query="What is the attendance policy?",
            detected_query_language="en",
        )
        assert resolved == "kn"

    def test_english_target_propagation(self):
        """4. English target propagation when explicitly requested."""
        resolved = resolve_response_language(
            explicit_target_language="en",
            query="What is the attendance policy?",
            detected_query_language="en",
        )
        assert resolved == "en"

    def test_english_query_to_telugu_response(self):
        """5. English query with explicit Telugu response target."""
        q = "What is the minimum attendance required?"
        resolved = resolve_response_language(
            explicit_target_language="te",
            query=q,
            detected_query_language="en",
        )
        assert resolved == "te"

    def test_english_query_to_hindi_response(self):
        """6. English query with explicit Hindi response target."""
        q = "What is the minimum attendance required?"
        resolved = resolve_response_language(
            explicit_target_language="hi",
            query=q,
            detected_query_language="en",
        )
        assert resolved == "hi"

    def test_english_query_to_kannada_response(self):
        """7. English query with explicit Kannada response target."""
        q = "What is the minimum attendance required?"
        resolved = resolve_response_language(
            explicit_target_language="kn",
            query=q,
            detected_query_language="en",
        )
        assert resolved == "kn"

    def test_telugu_query_to_english_response(self):
        """8. Telugu query with explicit English response target."""
        q = "విద్యార్థులకు పరీక్షలకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?"
        assert detect_query_language(q) == "te"
        resolved = resolve_response_language(
            explicit_target_language="en",
            query=q,
            detected_query_language="te",
        )
        assert resolved == "en"

    def test_auto_detect_infers_native_query_language(self):
        """Auto Detect correctly resolves to detected native query language."""
        q_te = "విద్యార్థులకు పరీక్షలకు హాజరు కావడానికి కనీస హాజరు ఎంత ఉండాలి?"
        assert resolve_response_language("auto", query=q_te) == "te"

        q_hi = "परीक्षा में शामिल होने के लिए न्यूनतम उपस्थिति कितनी होनी चाहिए?"
        assert resolve_response_language("auto", query=q_hi) == "hi"

        q_kn = "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಇರಬೇಕು?"
        assert resolve_response_language("auto", query=q_kn) == "kn"


class TestPositiveScriptValidation:
    """Tests 9-11: AnswerGuard script validation must reject pure English."""

    def test_english_answer_rejected_as_telugu(self):
        """9. Pure English answer rejected when target is Telugu."""
        eng_ans = "Students need 75% attendance to appear for semester exams. [Source 1]"
        assert not validate_target_language_script(eng_ans, "te")

    def test_english_answer_rejected_as_hindi(self):
        """10. Pure English answer rejected when target is Hindi."""
        eng_ans = "Students need 75% attendance to appear for semester exams. [Source 1]"
        assert not validate_target_language_script(eng_ans, "hi")

    def test_english_answer_rejected_as_kannada(self):
        """11. Pure English answer rejected when target is Kannada."""
        eng_ans = "Students need 75% attendance to appear for semester exams. [Source 1]"
        assert not validate_target_language_script(eng_ans, "kn")

    def test_pseudo_translation_prefix_rejected(self):
        """Fake 2-word Indic prefix on pure English text is rejected."""
        pseudo_te = "పత్రాల ప్రకారం: Students need 75% attendance. [Source 1]"
        assert not validate_target_language_script(pseudo_te, "te")

        pseudo_kn = "ದಾಖಲೆಗಳ ಪ್ರಕಾರ: Students need 75% attendance. [Source 1]"
        assert not validate_target_language_script(pseudo_kn, "kn")

        pseudo_hi = "दस्तावेज़ के अनुसार: Students need 75% attendance. [Source 1]"
        assert not validate_target_language_script(pseudo_hi, "hi")

    def test_valid_indic_answers_accepted(self):
        """Genuine Indic sentences with numbers, percentages and citations pass."""
        te_ans = "కోర్సుకు నమోదు చేసుకున్న విద్యార్థులు సెమిస్టర్ పరీక్షలకు హాజరు కావడానికి కనీసం 75% హాజరు కలిగి ఉండాలి. [Source 1]"
        assert validate_target_language_script(te_ans, "te")

        hi_ans = "सेमेस्टर परीक्षा में शामिल होने के लिए छात्र की न्यूनतम उपस्थिति 75% होनी चाहिए। [Source 1]"
        assert validate_target_language_script(hi_ans, "hi")

        kn_ans = "ಸೆಮಿಸ್ಟರ್ ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ವಿದ್ಯಾರ್ಥಿಯ ಕನಿಷ್ಠ ಹಾಜರಾತಿ 75% ಇರಬೇಕು. [Source 1]"
        assert validate_target_language_script(kn_ans, "kn")


class TestCitationsAndHonestFallbackStates:
    """Tests 20-22: Citations and fallback states."""

    def test_language_unavailable_has_zero_citations(self):
        """20. LANGUAGE_UNAVAILABLE state must have zero citations."""
        coord = RAGCoordinator()
        ans = coord._fallback_answer(
            query_id="q-test-1",
            reason="LANGUAGE_UNAVAILABLE",
            resp_lang="te",
            latency_ms=120.0,
        )
        assert ans.fallback_used is True
        assert ans.fallback_reason == "LANGUAGE_UNAVAILABLE"
        assert ans.grounded is False
        assert ans.sources == []
        assert ans.target_language == "te"
        assert ans.response_language == "te"
        assert "అందుబాటులో లేదు" in ans.answer_text

    def test_insufficient_evidence_has_zero_citations(self):
        """21. INSUFFICIENT_EVIDENCE state must have zero citations."""
        coord = RAGCoordinator()
        ans = coord._fallback_answer(
            query_id="q-test-2",
            reason="INSUFFICIENT_EVIDENCE",
            resp_lang="en",
            latency_ms=80.0,
        )
        assert ans.fallback_used is True
        assert ans.fallback_reason == "INSUFFICIENT_EVIDENCE"
        assert ans.grounded is False
        assert ans.sources == []

    def test_grounded_multilingual_answer_retains_citations(self):
        """22. Grounded multilingual answer retains citations properly."""
        sources = [
            SourceCitation(
                source_id="Source 1",
                chunk_id="chunk-1",
                doc_id="DOC-1",
                filename="Attendance_Policy.pdf",
                page_number=1,
            )
        ]
        ans = GroundedAnswer(
            query_id="q-test-3",
            answer_text="సెమిస్టర్ పరీక్షలకు హాజరు కావడానికి కనీసం 75% హాజరు తప్పనిసరి. [Source 1]",
            response_language="te",
            target_language="te",
            grounded=True,
            fallback_used=False,
            sources=sources,
        )
        assert ans.grounded is True
        assert len(ans.sources) == 1
        assert ans.sources[0].source_id == "Source 1"
        assert ans.target_language == "te"
