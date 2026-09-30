"""
Comprehensive RAG Battery Test Script
Tests the running FastAPI backend on all key dimensions:
  1. In-domain English grounded QA with citations
  2. Multilingual QA (Hindi, Kannada, Telugu)
  3. Domain policy facts (Attendance 75%, CGTMSE URL, MCA credits, Fees)
  4. Out-of-domain rejection (Cafeteria, Weather)
"""
import sys
import time
import requests

BASE_URL = "http://localhost:8000/api/v1/qa/query"

TESTS = [
    # --- In-Domain English ---
    {
        "id": "T01",
        "name": "Attendance Minimum (English)",
        "query": "What is the minimum attendance required?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": ["75"],
        "expect_citation": True,
    },
    {
        "id": "T02",
        "name": "Hostel Curfew (English)",
        "query": "What is the hostel curfew timing?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },
    {
        "id": "T03",
        "name": "Revaluation Fee (English)",
        "query": "What is the revaluation application fee?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },
    {
        "id": "T04",
        "name": "MCA Credits (English)",
        "query": "How many credits are required for the MCA degree?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },
    {
        "id": "T05",
        "name": "CGTMSE Website (URL Preservation)",
        "query": "What is the official website for CGTMSE?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": ["cgtmse.in"],
        "expect_citation": True,
    },
    {
        "id": "T06",
        "name": "Placement Eligibility (English)",
        "query": "What is required for campus placement eligibility?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },
    {
        "id": "T07",
        "name": "Malpractice Policy (English)",
        "query": "What happens if a student is caught cheating or committing malpractice?",
        "lang": "en",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },

    # --- Multilingual ---
    {
        "id": "T08",
        "name": "Attendance Hindi",
        "query": "न्यूनतम उपस्थिति कितनी होनी चाहिए?",
        "lang": "hi",
        "expected_grounded": True,
        "must_contain": ["75"],
        "expect_citation": True,
    },
    {
        "id": "T09",
        "name": "Hostel Curfew Hindi",
        "query": "हॉस्टल कर्फ्यू का समय क्या है?",
        "lang": "hi",
        "expected_grounded": True,
        "must_contain": [],
        "expect_citation": True,
    },
    {
        "id": "T10",
        "name": "Attendance Kannada",
        "query": "ಕನಿಷ್ಠ ಹಾಜರಾತಿ ಎಷ್ಟಿದೆ?",
        "lang": "kn",
        "expected_grounded": True,
        "must_contain": ["75"],
        "expect_citation": True,
    },
    {
        "id": "T11",
        "name": "Attendance Telugu",
        "query": "కనీస హాజరు ఎంత శాతం ఉండాలి?",
        "lang": "te",
        "expected_grounded": True,
        "must_contain": ["75"],
        "expect_citation": True,
    },

    # --- Out-of-Domain Rejections ---
    {
        "id": "T12",
        "name": "OOD Cafeteria Menu",
        "query": "What is the cafeteria menu for lunch today?",
        "lang": "en",
        "expected_grounded": False,
        "must_contain": ["Information Not Found"],
        "expect_citation": False,
    },
    {
        "id": "T13",
        "name": "OOD Bangalore Weather",
        "query": "What is the weather in Bangalore today?",
        "lang": "en",
        "expected_grounded": False,
        "must_contain": ["Information Not Found"],
        "expect_citation": False,
    },
]


def run_battery():
    passed = 0
    failed = 0
    total = len(TESTS)

    print("=" * 75)
    print("STARTING RAG CORE VERIFICATION BATTERY")
    print(f"Target: {BASE_URL}")
    print("=" * 75)

    for t in TESTS:
        test_id = t["id"]
        name = t["name"]
        query = t["query"]
        lang = t["lang"]
        exp_grounded = t["expected_grounded"]
        must_contain = t.get("must_contain", [])
        expect_citation = t.get("expect_citation", True)

        payload = {
            "query_text": query,
            "target_language": lang,
        }

        time.sleep(2.5)
        t0 = time.time()
        try:
            resp = requests.post(BASE_URL, json=payload, timeout=60)
            latency = (time.time() - t0) * 1000.0

            if resp.status_code != 200:
                print(f"❌ [{test_id}] {name} - HTTP {resp.status_code}: {resp.text[:100]}")
                failed += 1
                continue

            data = resp.json()
            answer = data.get("answer_text", "")
            grounded = data.get("grounded", False)
            citations = data.get("citations", [])
            state = data.get("response_state", "")

            # Verification logic
            reasons = []

            if grounded != exp_grounded:
                reasons.append(f"grounded={grounded} (expected {exp_grounded})")

            for mc in must_contain:
                if mc.lower() not in answer.lower():
                    reasons.append(f"missing '{mc}' in answer")

            if expect_citation and not citations:
                reasons.append("citations empty but expected")
            elif not expect_citation and citations:
                reasons.append(f"citations not empty ({len(citations)}) for OOD")

            if reasons:
                print(f"❌ [{test_id}] {name} ({latency:.0f}ms) - FAIL: {', '.join(reasons)}")
                print(f"     Query:  {query}")
                print(f"     Answer: {answer[:140]}...")
                failed += 1
            else:
                cit_info = f"({len(citations)} citations)" if citations else "(no citations)"
                print(f"✅ [{test_id}] {name} ({latency:.0f}ms) - PASS {cit_info}")
                print(f"     State:  {state}")
                print(f"     Answer: {answer[:130]}...")
                passed += 1

        except Exception as e:
            print(f"❌ [{test_id}] {name} - EXCEPTION: {e}")
            failed += 1

        time.sleep(0.5)

    print("=" * 75)
    print(f"BATTERY COMPLETE: {passed}/{total} PASSED, {failed} FAILED")
    print("=" * 75)

    return failed == 0


if __name__ == "__main__":
    success = run_battery()
    sys.exit(0 if success else 1)
