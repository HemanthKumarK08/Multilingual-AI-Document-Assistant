import urllib.request
import json
import time
import concurrent.futures

def send_qa(text, lang=None):
    start = time.perf_counter()
    req_data = json.dumps({"query_text": text, "target_language": lang}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/qa/query",
        data=req_data,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
    dur = (time.perf_counter() - start) * 1000.0
    return dur, res

print("=== MEASURING FIRST QUERY IMMEDIATELY AFTER STARTUP ===")
dur1, res1 = send_qa("What is the minimum attendance required for semester examinations?", "en")
print("Query 1 (en) Total Client Latency:", round(dur1, 2), "ms | Backend Retrieval:", res1.get("retrieval_latency_ms"), "ms | Backend Generation:", res1.get("generation_latency_ms"), "ms | Backend Total:", res1.get("total_latency_ms"), "ms")

print("\n=== MEASURING WARM MULTILINGUAL QUERIES ===")
dur2, res2 = send_qa("उपस्थिति नियम क्या हैं?", "hi")
print("Query 2 (hi) Total Client Latency:", round(dur2, 2), "ms | Backend Total:", res2.get("total_latency_ms"), "ms")

dur3, res3 = send_qa("ಹಾಜರಾತಿ ನಿಯಮಗಳು ಯಾವುವು?", "kn")
print("Query 3 (kn) Total Client Latency:", round(dur3, 2), "ms | Backend Total:", res3.get("total_latency_ms"), "ms")

dur4, res4 = send_qa("హాజరు నియమాలు ఏమిటి?", "te")
print("Query 4 (te) Total Client Latency:", round(dur4, 2), "ms | Backend Total:", res4.get("total_latency_ms"), "ms")

print("\n=== MEASURING CONCURRENT REQUESTS (QA + /HEALTH + ASSETS) ===")
with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
    def get_health():
        s = time.perf_counter()
        with urllib.request.urlopen("http://127.0.0.1:8000/health") as resp:
            resp.read()
        return (time.perf_counter() - s) * 1000.0

    def get_asset():
        s = time.perf_counter()
        with urllib.request.urlopen("http://127.0.0.1:8000/assets/index-DA3eFD5B.css") as resp:
            resp.read()
        return (time.perf_counter() - s) * 1000.0

    f_qa = executor.submit(send_qa, "Explain the grading system for undergraduate programs.", "en")
    time.sleep(0.005) # start health & asset while QA is executing in worker thread
    f_h1 = executor.submit(get_health)
    f_h2 = executor.submit(get_health)
    f_a1 = executor.submit(get_asset)

    qa_dur, qa_res = f_qa.result()
    h1_dur = f_h1.result()
    h2_dur = f_h2.result()
    a1_dur = f_a1.result()

print("Concurrent QA Total Duration:", round(qa_dur, 2), "ms")
print("Concurrent /health 1 Duration:", round(h1_dur, 2), "ms")
print("Concurrent /health 2 Duration:", round(h2_dur, 2), "ms")
print("Concurrent static CSS asset Duration:", round(a1_dur, 2), "ms")
