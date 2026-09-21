"""
Unit tests for RecursiveCharacterChunker covering natural boundaries, overlap,
multilingual Indic text (Hindi, Kannada, Telugu), and edge cases.
"""

import pytest

from app.services.chunking.models import ChunkingConfig
from app.services.chunking.recursive import RecursiveCharacterChunker


class TestRecursiveCharacterChunker:
    @pytest.fixture
    def default_chunker(self):
        config = ChunkingConfig(chunk_size=600, chunk_overlap=100, minimum_chunk_size=1)
        return RecursiveCharacterChunker(config=config)

    def test_short_text_single_chunk(self, default_chunker):
        text = "This is a short single paragraph document."
        chunks = default_chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].start_offset == 0
        assert chunks[0].end_offset == len(text)
        assert chunks[0].length == len(text)

    def test_empty_and_whitespace_text(self, default_chunker):
        assert default_chunker.chunk_text("") == []
        assert default_chunker.chunk_text("   \n\n\t  ") == []

    def test_exact_chunk_size_text(self):
        config = ChunkingConfig(chunk_size=50, chunk_overlap=10, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        text = "A" * 50
        chunks = chunker.chunk_text(text)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].length == 50

    def test_paragraph_boundary_splitting(self):
        config = ChunkingConfig(chunk_size=100, chunk_overlap=20, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        p1 = "First paragraph content that is moderately sized."
        p2 = "Second paragraph content that discusses another topic."
        p3 = "Third paragraph providing concluding remarks."
        text = f"{p1}\n\n{p2}\n\n{p3}"

        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2
        # Verify no chunk exceeds chunk_size
        for c in chunks:
            assert c.length <= config.chunk_size

    def test_sentence_boundary_splitting(self):
        config = ChunkingConfig(chunk_size=80, chunk_overlap=15, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        s1 = "This is the first sentence."
        s2 = "This is the second sentence."
        s3 = "This is the third sentence."
        s4 = "This is the fourth sentence."
        text = f"{s1} {s2} {s3} {s4}"

        chunks = chunker.chunk_text(text)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.length <= config.chunk_size

    def test_continuous_text_character_fallback(self):
        config = ChunkingConfig(chunk_size=50, chunk_overlap=10, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        # Continuous alphanumeric string with no whitespace/separators
        text = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789abcdefghijklmnopqrstuvwxyz" * 3
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1
        for c in chunks:
            assert c.length <= config.chunk_size

    def test_hindi_devanagari_chunking(self):
        config = ChunkingConfig(chunk_size=120, chunk_overlap=20, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        hindi_text = (
            "बैंगलोर इंस्टीट्यूट ऑफ टेक्नोलॉजी में आपका स्वागत है। "
            "यह संस्थान उच्च गुणवत्ता वाली तकनीकी शिक्षा प्रदान करता है। "
            "विभिन्न विभागों में कंप्यूटर विज्ञान, इलेक्ट्रॉनिक्स और मैकेनिकल इंजीनियरिंग शामिल हैं। "
            "छात्रों को पुस्तकालय, प्रयोगशालाएं और छात्रावास की आधुनिक सुविधाएं उपलब्ध कराई जाती हैं।"
        )
        chunks = chunker.chunk_text(hindi_text)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.length <= config.chunk_size
            assert len(c.text.strip()) > 0

    def test_kannada_script_chunking(self):
        config = ChunkingConfig(chunk_size=120, chunk_overlap=20, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        kannada_text = (
            "ಬೆಂಗಳೂರು ಇನ್‌ಸ್ಟಿಟ್ಯೂಟ್ ಆಫ್ ಟೆಕ್ನಾಲಜಿ (ಬಿಐಟಿ) ಗೆ ಸುಸ್ವಾಗತ. "
            "ಈ ಸಂಸ್ಥೆಯು ಗುಣಮಟ್ಟದ ತಾಂತ್ರಿಕ ಶಿಕ್ಷಣವನ್ನು ಒದಗಿಸುತ್ತದೆ. "
            "ಕಂಪ್ಯೂಟರ್ ಸೈನ್ಸ್, ಎಲೆಕ್ಟ್ರಾನಿಕ್ಸ್ ಮತ್ತು ಮೆಕ್ಯಾನಿಕಲ್ ಎಂಜಿನಿಯರಿಂಗ್ ವಿಭಾಗಗಳು ಇಲ್ಲಿವೆ. "
            "ವಿದ್ಯಾರ್ಥಿಗಳಿಗೆ ಸುಸಜ್ಜಿತ ಗ್ರಂಥಾಲಯ, ಪ್ರಯೋಗಾಲಯಗಳು ಮತ್ತು ವಸತಿ ನಿಲಯದ ಸೌಲಭ್ಯಗಳಿವೆ."
        )
        chunks = chunker.chunk_text(kannada_text)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.length <= config.chunk_size
            assert len(c.text.strip()) > 0

    def test_telugu_script_chunking(self):
        config = ChunkingConfig(chunk_size=120, chunk_overlap=20, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        telugu_text = (
            "బెంగళూరు ఇన్స్టిట్యూట్ ఆఫ్ టెక్నాలజీకి స్వాగతం. "
            "ఈ సంస్థ అత్యున్నత సాంకేతిక విద్యను అందిస్తుంది. "
            "కంప్యూటర్ సైన్స్, ఎలక్ట్రానిక్స్ మరియు మెకానికల్ ఇంజనీరింగ్ కోర్సులు అందుబాటులో ఉన్నాయి. "
            "విద్యార్థులకు ఆధునిక ప్రయోగశాలలు మరియు లైబ్రరీ సదుపాయాలు ఉన్నాయి."
        )
        chunks = chunker.chunk_text(telugu_text)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.length <= config.chunk_size
            assert len(c.text.strip()) > 0

    def test_code_mixed_indic_text(self):
        config = ChunkingConfig(chunk_size=100, chunk_overlap=15, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        mixed_text = (
            "BIT college mein MCA admission process shuru ho gaya hai. "
            "All students must submit their original documents before 15th August. "
            "Library fee and hostel admission form bhi official counter par available hai. "
            "Please check www.bit-bangalore.edu.in for further schedule details."
        )
        chunks = chunker.chunk_text(mixed_text)
        assert len(chunks) >= 2
        for c in chunks:
            assert c.length <= config.chunk_size

    def test_overlap_sliding_window(self):
        config = ChunkingConfig(chunk_size=60, chunk_overlap=20, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        text = "The quick brown fox jumps over the lazy dog. Jackdaws love my big sphinx of quartz."
        chunks = chunker.chunk_text(text)
        assert len(chunks) > 1
        # Check first chunk has start_offset 0
        assert chunks[0].start_offset == 0
        # Check that consecutive chunks have overlapping content
        for i in range(len(chunks) - 1):
            assert chunks[i].end_offset > chunks[i + 1].start_offset

    def test_zero_overlap_produces_disjoint_chunks(self):
        config = ChunkingConfig(chunk_size=50, chunk_overlap=0, minimum_chunk_size=1)
        chunker = RecursiveCharacterChunker(config=config)
        text = "First block of sentence. Second block of sentence. Third block of sentence."
        chunks = chunker.chunk_text(text)
        for i in range(len(chunks) - 1):
            assert chunks[i].end_offset <= chunks[i + 1].start_offset
