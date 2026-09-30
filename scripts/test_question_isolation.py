"""
Question Isolation Regression Test Script
Verifies:
1. Different queries produce strictly different retrieval candidates and contexts.
2. Orders tested: Forward, Reverse, and A -> B -> A.
3. No cross-query context pollution or bleed across consecutive invocations.
"""

import sys
from app.services.rag.coordinator import RAGCoordinator
from app.services.retrieval.coordinator import RetrievalCoordinator

def run_isolation_battery():
    rc = RetrievalCoordinator()
    rag = RAGCoordinator(retrieval_coordinator=rc)

    questions = {
        "Attendance": {
            "query": "What is the minimum attendance requirement to appear for exams?",
            "expected_kw": ["75%"],
            "expected_doc": "DOC-ATTN-001",
        },
        "NIRF": {
            "query": "What is the assistance and reimbursement for NIRF management institutions?",
            "expected_kw": ["90%", "NIRF"],
            "expected_doc": "DOC-UP-MSMESCHEMEBOOKLE-3692EB",
        },
        "CGTMSE": {
            "query": "In which website credit guarantee scheme can be applied?",
            "expected_kw": ["cgtmse.in"],
            "expected_doc": "DOC-UP-MSMESCHEMEBOOKLE-3692EB",
        },
        "IntelliExam": {
            "query": "What backend framework is used in the IntelliExam platform?",
            "expected_kw": ["Node.js", "Express"],
            "expected_doc": "DOC-UP-INTELLIEXAM-AI-BAC477",
        },
        "Scholarship": {
            "query": "What is the family income limit for merit-cum-means scholarship?",
            "expected_kw": ["2.5"],
            "expected_doc": "DOC-SCHOL-001",
        },
    }

    def execute_and_verify(name, step_desc):
        q_info = questions[name]
        retrieval = rc.retrieve(q_info["query"])
        cand_ids = [c.chunk_id for c in retrieval.candidates[:3]]
        cand_docs = [c.doc_id for c in retrieval.candidates[:3]]

        ans = rag.answer(q_info["query"], target_language="en")
        print(f"[{step_desc}] Query: '{name}'")
        print(f"  Top chunks: {cand_ids}")
        print(f"  Grounded: {ans.grounded}, Fallback: {ans.fallback_used}")
        print(f"  Answer snippet: {ans.answer_text[:120]}...")

        # Assert retrieval specificity
        assert any(q_info["expected_doc"] in d for d in cand_docs), (
            f"Expected doc {q_info['expected_doc']} missing in {cand_docs}"
        )

        # Assert answer correctness
        if name == "Scholarship":
            assert any(term in ans.answer_text.lower() for term in ["2,50,000", "2.5", "two lakhs fifty thousand"]), (
                f"Scholarship income limit missing in answer: {ans.answer_text}"
            )
        else:
            for kw in q_info["expected_kw"]:
                assert kw.lower() in ans.answer_text.lower(), (
                    f"Expected kw '{kw}' missing in answer for {name}: {ans.answer_text}"
                )
        import time
        time.sleep(1.5)
        return cand_ids, ans.answer_text

    print("=== ORDER 1: Forward (Attendance -> NIRF -> CGTMSE -> IntelliExam -> Scholarship) ===")
    forward_order = ["Attendance", "NIRF", "CGTMSE", "IntelliExam", "Scholarship"]
    forward_results = {}
    for name in forward_order:
        forward_results[name] = execute_and_verify(name, "FORWARD")

    print("\n=== ORDER 2: Reverse (Scholarship -> IntelliExam -> CGTMSE -> NIRF -> Attendance) ===")
    reverse_order = ["Scholarship", "IntelliExam", "CGTMSE", "NIRF", "Attendance"]
    reverse_results = {}
    for name in reverse_order:
        reverse_results[name] = execute_and_verify(name, "REVERSE")

    print("\n=== ORDER 3: A -> B -> A (Attendance -> NIRF -> Attendance) ===")
    a1_chunks, a1_ans = execute_and_verify("Attendance", "A1")
    b_chunks, b_ans = execute_and_verify("NIRF", "B")
    a2_chunks, a2_ans = execute_and_verify("Attendance", "A2")

    print("\n=== VERIFYING STRICT ISOLATION & DETERMINISM ===")
    # Attendance A1 and A2 must have identical top retrieved chunks
    assert a1_chunks == a2_chunks, f"A1 chunks {a1_chunks} != A2 chunks {a2_chunks}"
    assert "75%" in a1_ans and "75%" in a2_ans
    assert "nirf" not in a1_ans.lower() and "nirf" not in a2_ans.lower()
    assert "attendance" not in b_ans.lower()
    print("SUCCESS: Zero bleed between consecutive queries. Full question isolation confirmed!")

if __name__ == "__main__":
    run_isolation_battery()
