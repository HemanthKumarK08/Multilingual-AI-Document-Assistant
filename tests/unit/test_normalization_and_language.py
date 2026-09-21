"""
Unit Tests for Normalization and Language/Script Detection Modules
"""

import pytest
from app.services.ingestion.normalization import normalize_text, clean_heading_text
from app.services.ingestion.language import detect_script_and_language
from app.services.ingestion.constants import SupportedLanguage, ScriptType

def test_unicode_nfc_and_newline_normalization():
    raw = "Academic Regulations\r\n\r\n\r\n\r\nCourse Registration\r\n\tGrading System"
    normalized = normalize_text(raw)
    assert "\r" not in normalized
    assert "\n\n\n" not in normalized
    assert "Academic Regulations\n\nCourse Registration\n\tGrading System" == normalized

def test_control_character_removal_preserving_newlines_and_tabs():
    raw_with_control = "Header\x00\x07\x1B\nLine 1\tIndented\x7F\nLine 2"
    normalized = normalize_text(raw_with_control)
    assert "\x00" not in normalized
    assert "\x07" not in normalized
    assert "\x1B" not in normalized
    assert "\x7F" not in normalized
    assert "\n" in normalized
    assert "\t" in normalized
    assert "Header\nLine 1\tIndented\nLine 2" == normalized

def test_indic_script_preservation():
    # Hindi (Devanagari)
    hindi_text = "शैक्षणिक विनियम 2024 - छात्र उपस्थिति नियम"
    norm_hi = normalize_text(hindi_text)
    assert norm_hi == hindi_text

    # Kannada
    kannada_text = "ಪರೀಕ್ಷಾ ಮಾರ್ಗಸೂಚಿಗಳು ಮತ್ತು ಹಾಲ್ ಟಿಕೆಟ್ ನಿಯಮಗಳು"
    norm_kn = normalize_text(kannada_text)
    assert norm_kn == kannada_text

    # Telugu
    telugu_text = "స్కాలర్‌షిప్ మార్గదర్శకాలు మరియు అర్హత ప్రమాణాలు"
    norm_te = normalize_text(telugu_text)
    assert norm_te == telugu_text

def test_clean_heading_text():
    assert clean_heading_text("### 1.0 Academic Integrity Code") == "1.0 Academic Integrity Code"
    assert clean_heading_text("   ## Section 2: Grading System   ") == "Section 2: Grading System"
    assert clean_heading_text(None) == ""

def test_language_detection_english():
    text = "The minimum attendance requirement for all registered semester courses is 75% for students."
    res = detect_script_and_language(text)
    assert res.language == SupportedLanguage.ENGLISH.value
    assert res.script == ScriptType.LATIN.value
    assert res.confidence >= 0.70

def test_language_detection_hindi():
    text = "विद्यार्थियों के लिए प्रत्येक पाठ्यक्रम में न्यूनतम 75 प्रतिशत उपस्थिति अनिवार्य है।"
    res = detect_script_and_language(text)
    assert res.language == SupportedLanguage.HINDI.value
    assert res.script == ScriptType.DEVANAGARI.value
    assert res.confidence >= 0.90

def test_language_detection_kannada():
    text = "ಎಲ್ಲಾ ವಿದ್ಯಾರ್ಥಿಗಳು ಸೆಮಿಸ್ಟರ್ ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ 75% ಹಾಜರಾತಿಯನ್ನು ಹೊಂದಿರಬೇಕು."
    res = detect_script_and_language(text)
    assert res.language == SupportedLanguage.KANNADA.value
    assert res.script == ScriptType.KANNADA.value
    assert res.confidence >= 0.90

def test_language_detection_telugu():
    text = "పరీక్ష రాయడానికి అర్హత సాధించడానికి ప్రతి విద్యార్థికి కనీసం 75 శాతం హాజరు ఉండాలి."
    res = detect_script_and_language(text)
    assert res.language == SupportedLanguage.TELUGU.value
    assert res.script == ScriptType.TELUGU.value
    assert res.confidence >= 0.90

def test_language_detection_empty_or_indeterminate():
    assert detect_script_and_language("").language == SupportedLanguage.UNKNOWN.value
    assert detect_script_and_language("12345 67890 !@#$%^&*()").language == SupportedLanguage.UNKNOWN.value

def test_language_detection_romanized_and_mixed():
    # Romanized Hindi (Hinglish) -> Script is Latin, should not be falsely classified as native Devanagari
    hinglish_text = "Attendance kam hone par kya semester exam mein baithne diya jayega?"
    res_hinglish = detect_script_and_language(hinglish_text)
    assert res_hinglish.script == ScriptType.LATIN.value
    # Since it is Latin script without strong English markers, it defaults safely to English/Latin baseline metadata
    assert res_hinglish.language == SupportedLanguage.ENGLISH.value

    # Mixed script (English title with Kannada body)
    mixed_text = "HOSTEL POLICY 2024\nಹಾಸ್ಟೆಲ್ ಪ್ರವೇಶ ನಿಯಮಗಳು ಮತ್ತು ನಿಬಂಧನೆಗಳು."
    res_mixed = detect_script_and_language(mixed_text)
    assert res_mixed.script in (ScriptType.KANNADA.value, ScriptType.MIXED.value)

