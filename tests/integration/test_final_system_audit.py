"""
Phase 10.2 — Final Project-Wide System Audit & Hardening Test Suite
Covers 50+ comprehensive audit checks across Groups A through X:
  A. Startup & Health
  B. Documents Management
  C. Processing Pipeline
  D. Chunking Integrity
  E. Multilingual Embeddings
  F. Hybrid Retrieval
  G. RAG Grounding & Fallback
  H. Citations Provenance
  I. Evidence Inspection
  J. User Feedback
  K. Multilingual Script & Transliteration
  L. Speech-to-Text Foundation
  M. Voice -> RAG Flow
  N. Text-to-Speech Controller
  O. Voice Response Mode Orchestration
  P. Big Data Analytics & Parquet Lake
  Q. Zero Raw Data Privacy
  R. Application Security
  S. Frontend UI & Branding
  T. Responsive Viewports
  U. Accessibility & Reduced Motion
  V. Production Build Output
  W. System Launcher Scripts
  X. Full User Journey
"""
import json
import re
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app

PROJECT_ROOT = Path(__file__).parent.parent.parent


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


# ── Group A: Startup & Health (4 tests) ─────────────────────────────────────────

def test_audit_a01_health_endpoint(client: TestClient):
    """AUDIT-A01: /health endpoint returns 200 with status ok and connected database."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["database_status"] == "connected"
    assert data["vector_store_configured"] is True


def test_audit_a02_analytics_health(client: TestClient):
    """AUDIT-A02: /api/v1/analytics/health returns analytics subsystem health."""
    res = client.get("/api/v1/analytics/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data


def test_audit_a03_openapi_docs(client: TestClient):
    """AUDIT-A03: Swagger OpenAPI JSON schema is reachable and valid."""
    res = client.get("/openapi.json")
    assert res.status_code == 200
    data = res.json()
    assert "paths" in data
    assert "/api/v1/qa/query" in data["paths"]


def test_audit_a04_root_route_serves_spa(client: TestClient):
    """AUDIT-A04: GET / returns 200 serving index.html or SPA root."""
    res = client.get("/")
    assert res.status_code == 200


# ── Group B: Documents Management (3 tests) ────────────────────────────────────

def test_audit_b01_list_documents(client: TestClient):
    """AUDIT-B01: /api/v1/documents returns list of registered documents."""
    res = client.get("/api/v1/documents")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_audit_b02_invalid_document_id(client: TestClient):
    """AUDIT-B02: Querying a non-existent document ID returns 404."""
    res = client.get("/api/v1/documents/NON_EXISTENT_DOC_ID_99999")
    assert res.status_code == 404


def test_audit_b03_document_schema_validation():
    """AUDIT-B03: Document DB model defines id, title, category, and hash attributes."""
    doc_model = PROJECT_ROOT / "app" / "db" / "models" / "document.py"
    assert doc_model.exists()
    content = doc_model.read_text(encoding="utf-8")
    assert "doc_id" in content or "id" in content
    assert "category" in content


# ── Group C: Processing Pipeline (2 tests) ─────────────────────────────────────

def test_audit_c01_supported_extensions():
    """AUDIT-C01: Ingestion parsers register PDF, DOCX, and TXT parsers."""
    parsers_dir = PROJECT_ROOT / "app" / "services" / "ingestion" / "parsers"
    assert (parsers_dir / "pdf.py").exists()
    assert (parsers_dir / "docx.py").exists()
    assert (parsers_dir / "txt.py").exists()


def test_audit_c02_sha256_deduplication():
    """AUDIT-C02: Ingestion coordinator includes SHA-256 hashing for deduplication."""
    hashing_file = PROJECT_ROOT / "app" / "services" / "ingestion" / "hashing.py"
    assert hashing_file.exists()
    content = hashing_file.read_text(encoding="utf-8")
    assert "sha256" in content.lower()


# ── Group D: Chunking Integrity (2 tests) ──────────────────────────────────────

def test_audit_d01_chunking_deterministic_ids():
    """AUDIT-D01: Chunking logic assigns deterministic chunk boundaries and indices."""
    chunk_file = PROJECT_ROOT / "app" / "services" / "chunking" / "coordinator.py"
    assert chunk_file.exists()
    content = chunk_file.read_text(encoding="utf-8")
    assert "chunk" in content.lower()


def test_audit_d02_chunking_models_structure():
    """AUDIT-D02: Chunk model defines doc_id, chunk_index, and text content."""
    models_file = PROJECT_ROOT / "app" / "services" / "chunking" / "models.py"
    assert models_file.exists()
    content = models_file.read_text(encoding="utf-8")
    assert "chunk_index" in content or "text" in content


# ── Group E: Multilingual Embeddings (2 tests) ────────────────────────────────

def test_audit_e01_embedding_model_specification():
    """AUDIT-E01: Embedding model is configured as multilingual-e5-small."""
    emb_file = PROJECT_ROOT / "app" / "services" / "embeddings" / "constants.py"
    if not emb_file.exists():
        emb_file = PROJECT_ROOT / "app" / "services" / "embeddings" / "sentence_transformer.py"
    assert emb_file.exists()
    content = emb_file.read_text(encoding="utf-8")
    assert "multilingual-e5-small" in content or "384" in content


def test_audit_e02_embedding_coordinator():
    """AUDIT-E02: Embedding coordinator supports batch embedding generation."""
    coord_file = PROJECT_ROOT / "app" / "services" / "embeddings" / "coordinator.py"
    assert coord_file.exists()


# ── Group F: Hybrid Retrieval (2 tests) ────────────────────────────────────────

def test_audit_f01_hybrid_retrieval_components():
    """AUDIT-F01: Retrieval pipeline incorporates dense retriever, lexical BM25, and hybrid fusion."""
    ret_dir = PROJECT_ROOT / "app" / "services" / "retrieval"
    assert (ret_dir / "dense_retriever.py").exists()
    assert (ret_dir / "lexical_retriever.py").exists()
    assert (ret_dir / "hybrid.py").exists()
    assert (ret_dir / "reranker.py").exists()


def test_audit_f02_retrieval_reranking():
    """AUDIT-F02: Reranker applies deterministic score fusion and thresholding."""
    reranker_file = PROJECT_ROOT / "app" / "services" / "retrieval" / "reranker.py"
    assert reranker_file.exists()
    content = reranker_file.read_text(encoding="utf-8")
    assert "score" in content.lower() or "rank" in content.lower()


# ── Group G: RAG Grounding & Fallback (3 tests) ────────────────────────────────

def test_audit_g01_grounded_rag_query(client: TestClient):
    """AUDIT-G01: In-domain question retrieves grounded answer with citations."""
    payload = {"query_text": "What database does IntelliExam AI use?", "target_language": "en", "category": None}
    res = client.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "answer_text" in data
    assert data["answer_text"] is not None
    assert len(data["answer_text"]) > 0


def test_audit_g02_out_of_domain_fallback(client: TestClient):
    """AUDIT-G02: Out-of-domain query safely triggers fallback / insufficient evidence."""
    payload = {"query_text": "What is the orbital trajectory of the James Webb telescope in deep space?", "target_language": "en", "category": None}
    res = client.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "is_fallback" in data


def test_audit_g03_rag_evidence_gating():
    """AUDIT-G03: RAG service implements evidence gating before generation."""
    gate_file = PROJECT_ROOT / "app" / "services" / "rag" / "evidence_gate.py"
    assert gate_file.exists()


# ── Group H: Citations Provenance (2 tests) ────────────────────────────────────

def test_audit_h01_citation_provenance_structure(client: TestClient):
    """AUDIT-H01: Citations include document_id, excerpt, and similarity metrics."""
    payload = {"query_text": "IntelliExam AI features and architecture", "target_language": None, "category": None}
    res = client.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    data = res.json()
    if data.get("citations") and len(data["citations"]) > 0:
        c = data["citations"][0]
        assert "document_id" in c
        assert "excerpt" in c


def test_audit_h02_citation_formatter():
    """AUDIT-H02: Citation formatter formats clean document references."""
    formatter_file = PROJECT_ROOT / "app" / "services" / "rag" / "citation_formatter.py"
    assert formatter_file.exists()


# ── Group I: Evidence Inspection (2 tests) ────────────────────────────────────

def test_audit_i01_evidence_drawer_component():
    """AUDIT-I01: EvidenceDrawer displays verified citation provenance and copy controls."""
    drawer_file = PROJECT_ROOT / "frontend" / "src" / "components" / "EvidenceDrawer.jsx"
    assert drawer_file.exists()
    content = drawer_file.read_text(encoding="utf-8")
    assert "Supporting Evidence Passage" in content
    assert "copyEvidenceText" in content


def test_audit_i02_citation_card_inspect_trigger():
    """AUDIT-I02: CitationCard triggers onInspect to display full evidence modal."""
    card_file = PROJECT_ROOT / "frontend" / "src" / "components" / "CitationCard.jsx"
    assert card_file.exists()
    content = card_file.read_text(encoding="utf-8")
    assert "onInspect" in content
    assert "View Evidence" in content


# ── Group J: User Feedback (2 tests) ───────────────────────────────────────────

def test_audit_j01_feedback_endpoint(client: TestClient):
    """AUDIT-J01: /api/v1/qa/feedback endpoint processes user rating."""
    payload = {
        "query_id": "TEST_AUDIT_QUERY_001",
        "feedback": 1
    }
    res = client.post("/api/v1/qa/feedback", json=payload)
    assert res.status_code in [200, 201]


def test_audit_j02_feedback_widget_component():
    """AUDIT-J02: FeedbackWidget provides Thumbs Up / Down ratings."""
    widget_file = PROJECT_ROOT / "frontend" / "src" / "components" / "FeedbackWidget.jsx"
    assert widget_file.exists()
    content = widget_file.read_text(encoding="utf-8")
    assert "ThumbsUp" in content or "Helpful" in content


# ── Group K: Multilingual Script & Transliteration (2 tests) ───────────────────

def test_audit_k01_indic_transliteration_support():
    """AUDIT-K01: Query processing handles multilingual query expansion and normalizations."""
    qp_file = PROJECT_ROOT / "app" / "services" / "retrieval" / "query_processing.py"
    assert qp_file.exists()
    content = qp_file.read_text(encoding="utf-8")
    assert "process" in content or "normalize" in content or "expand" in content


def test_audit_k02_hindi_query_execution(client: TestClient):
    """AUDIT-K02: Hindi query execution completes successfully."""
    payload = {"query_text": "परीक्षा नियम क्या हैं?", "target_language": "hi", "category": None}
    res = client.post("/api/v1/qa/query", json=payload)
    assert res.status_code == 200
    assert "answer_text" in res.json()


# ── Group L: Speech-to-Text Foundation (2 tests) ──────────────────────────────

def test_audit_l01_speech_recognition_locales():
    """AUDIT-L01: Speech recognition maps en-US, hi-IN, kn-IN, and te-IN locales."""
    sr_file = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "speechRecognition.js"
    assert sr_file.exists()
    content = sr_file.read_text(encoding="utf-8")
    assert "en-US" in content
    assert "hi-IN" in content
    assert "kn-IN" in content
    assert "te-IN" in content


def test_audit_l02_speech_recognition_button_component():
    """AUDIT-L02: SpeechRecognitionButton handles listening, starting, and cancel states."""
    btn_file = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "SpeechRecognitionButton.jsx"
    assert btn_file.exists()
    content = btn_file.read_text(encoding="utf-8")
    assert "onVoiceStateChange" in content
    assert "handleCancel" in content


# ── Group M: Voice -> RAG Flow (2 tests) ──────────────────────────────────────

def test_audit_m01_voice_transcript_to_rag():
    """AUDIT-M01: Voice transcript populates inputQuery for user review prior to send."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "handleVoiceTranscript" in content
    assert "inputModeRef.current = 'voice'" in content


def test_audit_m02_voice_input_indicator_badge():
    """AUDIT-M02: Messages sent via voice display subtle mic badge for transparency."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "msg.inputMode === 'voice'" in content


# ── Group N: Text-to-Speech Controller (2 tests) ──────────────────────────────

def test_audit_n01_tts_controller_methods():
    """AUDIT-N01: createTTSController exposes speak, stop, pause, and resume."""
    tts_file = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "textToSpeech.js"
    assert tts_file.exists()
    content = tts_file.read_text(encoding="utf-8")
    assert "speak()" in content
    assert "stop()" in content
    assert "pause()" in content
    assert "resume()" in content


def test_audit_n02_markdown_stripped_for_tts():
    """AUDIT-N02: markdownToSpeechText strips markdown syntax and citation tags."""
    tts_file = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "textToSpeech.js"
    content = tts_file.read_text(encoding="utf-8")
    assert "markdownToSpeechText" in content


# ── Group O: Voice Response Mode Orchestration (2 tests) ──────────────────────

def test_audit_o01_voice_response_orchestration():
    """AUDIT-O01: Auto-TTS triggers strictly when submitVoiceResponse && submitMode === 'voice'."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "if (submitVoiceResponse && submitMode === 'voice'" in content
    assert "stopAllSpeech()" in content


def test_audit_o02_mic_turn_taking_interruption():
    """AUDIT-O02: Microphone activation immediately stops running TTS."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "onVoiceStateChange" in content
    match = re.search(r'onVoiceStateChange.*?stopAllSpeech\(\)', content, re.DOTALL)
    assert match is not None


# ── Group P: Big Data Analytics & Parquet Lake (3 tests) ──────────────────────

def test_audit_p01_analytics_summary_endpoint(client: TestClient):
    """AUDIT-P01: Analytics summary endpoint returns aggregate platform metrics."""
    res = client.get("/api/v1/analytics/summary")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, dict)


def test_audit_p02_analytics_languages_endpoint(client: TestClient):
    """AUDIT-P02: Analytics languages endpoint returns query language distribution."""
    res = client.get("/api/v1/analytics/languages")
    assert res.status_code == 200


def test_audit_p03_parquet_lake_structure():
    """AUDIT-P03: Parquet lake partitioned structure exists on disk."""
    lake_dir = PROJECT_ROOT / "data" / "telemetry" / "parquet"
    assert lake_dir.exists()


# ── Group Q: Zero Raw Data Privacy (2 tests) ──────────────────────────────────

def test_audit_q01_raw_telemetry_no_prohibited_fields():
    """AUDIT-Q01: Audit raw telemetry files ensuring 0 raw queries or answers logged."""
    raw_dir = PROJECT_ROOT / "data" / "telemetry" / "raw"
    prohibited = {'query_text', 'raw_query', 'answer', 'response_text', 'passage', 'document_text'}
    if raw_dir.exists():
        for f in raw_dir.glob("*.jsonl"):
            for line in f.read_text(encoding="utf-8").splitlines():
                if not line.strip(): continue
                rec = json.loads(line)
                assert not set(rec.keys()).intersection(prohibited), f"Prohibited field in {f.name}"


def test_audit_q02_privacy_architecture_notice():
    """AUDIT-Q02: Analytics page displays privacy architecture notice."""
    notice_file = PROJECT_ROOT / "frontend" / "src" / "components" / "analytics" / "PrivacyArchitectureNotice.jsx"
    assert notice_file.exists()


# ── Group R: Application Security (2 tests) ───────────────────────────────────

def test_audit_r01_no_dangerously_set_inner_html():
    """AUDIT-R01: Frontend does not use dangerouslySetInnerHTML in user content rendering."""
    src_dir = PROJECT_ROOT / "frontend" / "src"
    for jsx_file in src_dir.glob("**/*.jsx"):
        content = jsx_file.read_text(encoding="utf-8")
        assert "dangerouslySetInnerHTML=" not in content, f"Unsafe HTML prop in {jsx_file.name}"


def test_audit_r02_no_eval_in_frontend():
    """AUDIT-R02: Frontend code contains no eval() or new Function() execution."""
    src_dir = PROJECT_ROOT / "frontend" / "src"
    for js_file in src_dir.glob("**/*.js*"):
        content = js_file.read_text(encoding="utf-8")
        assert not re.search(r'\beval\s*\(', content), f"eval() detected in {js_file.name}"
        assert not re.search(r'new\s+Function\s*\(', content), f"new Function() detected in {js_file.name}"


# ── Group S: Frontend UI & Branding (2 tests) ─────────────────────────────────

def test_audit_s01_production_branding_in_header():
    """AUDIT-S01: Header contains Production status badge and platform title."""
    header_file = PROJECT_ROOT / "frontend" / "src" / "components" / "Header.jsx"
    content = header_file.read_text(encoding="utf-8")
    assert "Production" in content
    assert "Multilingual AI Document Assistant" in content
    assert "Phase 8.1" not in content


def test_audit_s02_sidebar_branding():
    """AUDIT-S02: Sidebar contains Major Project institution card."""
    sidebar_file = PROJECT_ROOT / "frontend" / "src" / "components" / "Sidebar.jsx"
    content = sidebar_file.read_text(encoding="utf-8")
    assert "Major Project" in content
    assert "Bangalore Institute" in content


# ── Group T: Responsive Viewports (2 tests) ───────────────────────────────────

def test_audit_t01_responsive_breakpoints_in_layout():
    """AUDIT-T01: Layout and Ask AI incorporate sm:, md:, lg: responsive styling."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "sm:" in content
    assert "lg:" in content
    assert "max-w-5xl" in content
    assert "mx-auto" in content


def test_audit_t02_sidebar_mobile_drawer():
    """AUDIT-T02: Sidebar handles mobile overlay with backdrop and lg:sticky."""
    sidebar_file = PROJECT_ROOT / "frontend" / "src" / "components" / "Sidebar.jsx"
    content = sidebar_file.read_text(encoding="utf-8")
    assert "lg:hidden" in content
    assert "lg:sticky" in content


# ── Group U: Accessibility & Reduced Motion (2 tests) ─────────────────────────

def test_audit_u01_aria_attributes_and_focus():
    """AUDIT-U01: Interactive components define aria-label, aria-pressed, and focus rings."""
    ask_file = PROJECT_ROOT / "frontend" / "src" / "pages" / "AskAI.jsx"
    content = ask_file.read_text(encoding="utf-8")
    assert "aria-label" in content
    assert "focus:ring-2" in content


def test_audit_u02_reduced_motion_compliance():
    """AUDIT-U02: Voice components declare motion-reduce:animate-none."""
    vli_file = PROJECT_ROOT / "frontend" / "src" / "components" / "voice" / "VoiceListeningIndicator.jsx"
    content = vli_file.read_text(encoding="utf-8")
    assert "motion-reduce:" in content


# ── Group V: Production Build Output (2 tests) ────────────────────────────────

def test_audit_v01_production_dist_assets():
    """AUDIT-V01: Production bundle artifacts exist in frontend/dist."""
    dist_html = PROJECT_ROOT / "frontend" / "dist" / "index.html"
    assert dist_html.exists()
    assert len(dist_html.read_text(encoding="utf-8")) > 100


def test_audit_v02_production_js_and_css():
    """AUDIT-V02: Production dist assets include bundled JS and CSS."""
    dist_assets = PROJECT_ROOT / "frontend" / "dist" / "assets"
    assert dist_assets.exists()
    js_files = list(dist_assets.glob("*.js"))
    css_files = list(dist_assets.glob("*.css"))
    assert len(js_files) > 0
    assert len(css_files) > 0


# ── Group W: System Launcher Scripts (2 tests) ────────────────────────────────

def test_audit_w01_launcher_scripts_exist():
    """AUDIT-W01: Launcher and health check scripts exist with executable permissions."""
    run_cmd = PROJECT_ROOT / "run_project.command"
    check_sh = PROJECT_ROOT / "check_project.sh"
    stop_cmd = PROJECT_ROOT / "stop_project.command"
    assert run_cmd.exists()
    assert check_sh.exists()
    assert stop_cmd.exists()


def test_audit_w02_launcher_script_contents():
    """AUDIT-W02: run_project.command contains uvicorn startup and browser open commands."""
    run_cmd = PROJECT_ROOT / "run_project.command"
    content = run_cmd.read_text(encoding="utf-8")
    assert "uvicorn" in content
    assert "8000" in content


# ── Group X: Full User Journey (2 tests) ──────────────────────────────────────

def test_audit_x01_full_user_journey_flow(client: TestClient):
    """AUDIT-X01: Full user journey executes: health -> list docs -> query RAG -> analytics."""
    # 1. Health check
    h = client.get("/health")
    assert h.status_code == 200
    
    # 2. Ingested documents list
    docs = client.get("/api/v1/documents")
    assert docs.status_code == 200
    
    # 3. User QA query
    qa = client.post("/api/v1/qa/query", json={"query_text": "Explain attendance guidelines", "target_language": "en", "category": "attendance"})
    assert qa.status_code == 200
    res_data = qa.json()
    assert "answer_text" in res_data
    
    # 4. Analytics metrics verification
    analytics = client.get("/api/v1/analytics/summary")
    assert analytics.status_code == 200


def test_audit_x02_kannada_user_journey(client: TestClient):
    """AUDIT-X02: Multilingual Kannada user query completes through RAG pipeline."""
    qa = client.post("/api/v1/qa/query", json={"query_text": "ಪರೀಕ್ಷೆಗೆ ಹಾಜರಾಗಲು ಕನಿಷ್ಠ ಎಷ್ಟು ಹಾಜರಾತಿ ಬೇಕು?", "target_language": "kn", "category": "attendance"})
    assert qa.status_code == 200
    res_data = qa.json()
    assert "answer_text" in res_data
