"""
Multilingual Regression Test Script
Verifies:
1. English -> English
2. English -> Hindi (Devanagari script)
3. English -> Kannada (Kannada script)
4. English -> Telugu (Telugu script)
5. Hindi -> Hindi
6. Kannada -> Kannada
7. Telugu -> Telugu
8. Romanized Hindi
9. Romanized Kannada
10. Romanized Telugu
Asserts actual text script purity, not just language metadata.
"""

import re
import time
from app.services.rag.coordinator import RAGCoordinator
from app.services.retrieval.coordinator import RetrievalCoordinator

HI_RE = re.compile(r"[\u0900-\u097F]")
KN_RE = re.compile(r"[\u0C80-\u0CFF]")
TE_RE = re.compile(r"[\u0C00-\u0C7F]")

def run_multilingual_tests():
    rag = RAGCoordinator()

    test_cases = [
        # Cross-language
        {"id": "EN->EN", "query": "What is the minimum attendance required?", "target": "en", "script": "en"},
        {"id": "EN->HI", "query": "What is the minimum attendance required?", "target": "hi", "script": "hi"},
        {"id": "EN->KN", "query": "What is the minimum attendance required?", "target": "kn", "script": "kn"},
        {"id": "EN->TE", "query": "What is the minimum attendance required?", "target": "te", "script": "te"},

        # Native-to-native
        {"id": "HI->HI", "query": "परीक्षा के लिए न्यूनतम उपस्थिति कितनी आवश्यक है?", "target": "hi", "script": "hi"},
        {"id": "KN->KN", "query": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟು ಬೇಕು?", "target": "kn", "script": "kn"},
        {"id": "TE->TE", "query": "పరీక్షలకు హాಜరు కావడానికి కనీస హాಜరు ఎంత శాతం ఉండాలి?", "target": "te", "script": "te"},

        # Romanized Indic
        {"id": "RM-HI", "query": "pariksha ke liye minimum attendance kitna chahiye?", "target": "hi", "script": "hi"},
        {"id": "RM-KN", "query": "exam ge attend agalu minimum attendance eshtu beku?", "target": "kn", "script": "kn"},
        {"id": "RM-TE", "query": "exams ki attend avvadaniki minimum attendance entha undali?", "target": "te", "script": "te"},
    ]

    passed = 0
    total = len(test_cases)

    for tc in test_cases:
        ans = rag.answer(tc["query"], target_language=tc["target"])
        text = ans.answer_text
        print(f"[{tc['id']}] Target: {tc['target']} | Answer: {text[:100]}...")

        assert ans.grounded is True, f"Failed grounding on {tc['id']}"
        assert len(ans.sources) > 0, f"No sources cited on {tc['id']}"

        # Verify script purity on actual answer text
        if tc["script"] == "hi":
            assert HI_RE.search(text) is not None, f"Devanagari missing in {tc['id']}"
            assert KN_RE.search(text) is None, f"Kannada contamination in Hindi on {tc['id']}"
            assert TE_RE.search(text) is None, f"Telugu contamination in Hindi on {tc['id']}"
        elif tc["script"] == "kn":
            assert KN_RE.search(text) is not None, f"Kannada missing in {tc['id']}"
            assert HI_RE.search(text) is None, f"Devanagari contamination in Kannada on {tc['id']}"
            assert TE_RE.search(text) is None, f"Telugu contamination in Kannada on {tc['id']}"
        elif tc["script"] == "te":
            assert TE_RE.search(text) is not None, f"Telugu missing in {tc['id']}"
            assert HI_RE.search(text) is None, f"Devanagari contamination in Telugu on {tc['id']}"
            assert KN_RE.search(text) is None, f"Kannada contamination in Telugu on {tc['id']}"
        elif tc["script"] == "en":
            assert HI_RE.search(text) is None, f"Indic script in English on {tc['id']}"
            assert KN_RE.search(text) is None, f"Indic script in English on {tc['id']}"
            assert TE_RE.search(text) is None, f"Indic script in English on {tc['id']}"

        passed += 1
        time.sleep(2.0)  # Paced for Gemini Free Tier

    print(f"\nMULTILINGUAL REGRESSION: {passed}/{total} PASSED with 100% script purity!")

if __name__ == "__main__":
    run_multilingual_tests()
