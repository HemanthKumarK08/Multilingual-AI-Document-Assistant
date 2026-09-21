"""
User-Facing Application Entry Page (Pre-Phase 8)
Provides a clean, modern landing page for the Multilingual AI Document Assistant.
"""

def get_landing_page_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Multilingual AI Document Assistant</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #0a0f1d;
            --bg-surface: #111827;
            --bg-card: rgba(17, 24, 39, 0.7);
            --border-color: rgba(255, 255, 255, 0.08);
            --border-hover: rgba(99, 102, 241, 0.4);
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-amber: #f59e0b;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --text-subtle: #6b7280;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background-color: var(--bg-base);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            background-image: 
                radial-gradient(circle at 15% 15%, rgba(99, 102, 241, 0.12) 0%, transparent 40%),
                radial-gradient(circle at 85% 25%, rgba(6, 182, 212, 0.1) 0%, transparent 40%),
                radial-gradient(circle at 50% 85%, rgba(139, 92, 246, 0.08) 0%, transparent 50%);
            background-attachment: fixed;
            line-height: 1.5;
        }

        .container {
            max-width: 1080px;
            margin: 0 auto;
            padding: 2.5rem 1.5rem;
            flex: 1;
            display: flex;
            flex-direction: column;
        }

        /* Header */
        header {
            text-align: center;
            margin-bottom: 3rem;
        }

        .badge-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(99, 102, 241, 0.12);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #a5b4fc;
            padding: 0.35rem 0.9rem;
            border-radius: 9999px;
            font-size: 0.8125rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
            margin-bottom: 1.25rem;
        }

        .badge-tag span.dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background-color: #818cf8;
            box-shadow: 0 0 8px #818cf8;
        }

        h1 {
            font-size: 2.5rem;
            font-weight: 800;
            letter-spacing: -0.025em;
            background: linear-gradient(135deg, #ffffff 30%, #a5b4fc 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.75rem;
        }

        .subtitle {
            font-size: 1.125rem;
            color: var(--text-muted);
            max-width: 650px;
            margin: 0 auto;
            font-weight: 400;
        }

        /* Primary Action Cards Grid */
        .cards-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .card {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.75rem;
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            transition: all 0.25s ease;
            position: relative;
            overflow: hidden;
        }

        .card:hover {
            border-color: var(--border-hover);
            transform: translateY(-3px);
            box-shadow: 0 12px 28px -6px rgba(0, 0, 0, 0.5), 0 0 1px 1px rgba(99, 102, 241, 0.2);
        }

        .card-icon {
            font-size: 2.25rem;
            margin-bottom: 1rem;
            display: inline-block;
        }

        .card-title {
            font-size: 1.25rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.5rem;
        }

        .card-desc {
            color: var(--text-muted);
            font-size: 0.9375rem;
            margin-bottom: 1.5rem;
            flex-grow: 1;
        }

        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            background: var(--primary);
            color: #ffffff;
            padding: 0.7rem 1.25rem;
            border-radius: 0.625rem;
            font-weight: 600;
            font-size: 0.9375rem;
            text-decoration: none;
            border: none;
            cursor: pointer;
            transition: all 0.2s ease;
            width: 100%;
        }

        .btn:hover {
            background: var(--primary-hover);
            box-shadow: 0 4px 14px rgba(99, 102, 241, 0.4);
        }

        .btn-outline {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-main);
        }

        .btn-outline:hover {
            background: rgba(255, 255, 255, 0.1);
            border-color: rgba(255, 255, 255, 0.2);
            box-shadow: none;
        }

        /* Status & Developer Tools Section */
        .bottom-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
        }

        .section-card {
            background: rgba(17, 24, 39, 0.5);
            border: 1px solid var(--border-color);
            border-radius: 1rem;
            padding: 1.5rem;
            backdrop-filter: blur(8px);
        }

        .section-header {
            font-size: 1rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 1rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }

        /* Status items */
        .status-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 0.75rem;
        }

        .status-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(0, 0, 0, 0.25);
            padding: 0.625rem 0.875rem;
            border-radius: 0.5rem;
            border: 1px solid rgba(255, 255, 255, 0.04);
            font-size: 0.875rem;
        }

        .status-label {
            color: var(--text-muted);
            font-weight: 500;
        }

        .status-value {
            display: flex;
            align-items: center;
            gap: 0.375rem;
            font-weight: 600;
            color: var(--accent-green);
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background-color: var(--accent-green);
            box-shadow: 0 0 6px var(--accent-green);
        }

        .status-dot.loading {
            background-color: var(--accent-amber);
            box-shadow: 0 0 6px var(--accent-amber);
        }

        /* Dev links */
        .dev-links {
            display: flex;
            flex-direction: column;
            gap: 0.625rem;
        }

        .dev-link-btn {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            padding: 0.625rem 0.875rem;
            border-radius: 0.5rem;
            color: var(--text-main);
            text-decoration: none;
            font-size: 0.875rem;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .dev-link-btn:hover {
            background: rgba(99, 102, 241, 0.1);
            border-color: rgba(99, 102, 241, 0.3);
            color: #ffffff;
        }

        .dev-link-btn span.badge {
            background: rgba(99, 102, 241, 0.2);
            color: #a5b4fc;
            padding: 0.125rem 0.5rem;
            border-radius: 0.25rem;
            font-size: 0.75rem;
            font-family: monospace;
        }

        /* Modal / Notification Dialog */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(4px);
            display: none;
            align-items: center;
            justify-content: center;
            padding: 1.5rem;
            z-index: 100;
        }

        .modal {
            background: #111827;
            border: 1px solid rgba(99, 102, 241, 0.3);
            border-radius: 1rem;
            max-width: 480px;
            width: 100%;
            padding: 2rem;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.8);
            text-align: center;
            animation: modalFadeIn 0.2s ease-out;
        }

        @keyframes modalFadeIn {
            from { opacity: 0; transform: scale(0.95); }
            to { opacity: 1; transform: scale(1); }
        }

        .modal-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }

        .modal-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.75rem;
            color: #ffffff;
        }

        .modal-desc {
            color: var(--text-muted);
            font-size: 0.9375rem;
            line-height: 1.5;
            margin-bottom: 1.5rem;
        }

        footer {
            text-align: center;
            padding: 2rem 0 1rem;
            color: var(--text-subtle);
            font-size: 0.8125rem;
        }

        @media (max-width: 640px) {
            h1 { font-size: 1.875rem; }
            .status-grid { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <header>
            <div class="badge-tag">
                <span class="dot"></span>
                MCA Major Project • with Big Data Analytics
            </div>
            <h1>Multilingual AI Document Assistant</h1>
            <p class="subtitle">AI-powered multilingual document understanding and question answering</p>
        </header>

        <!-- Main Action Cards -->
        <div class="cards-grid">
            <!-- 1. Documents -->
            <div class="card">
                <div>
                    <span class="card-icon">📄</span>
                    <h2 class="card-title">Documents</h2>
                    <p class="card-desc">Upload and manage institutional documents (PDF, DOCX, TXT) for intelligent multilingual indexing and search.</p>
                </div>
                <button class="btn" onclick="showFeatureModal('Documents Management', 'The complete visual document upload and management dashboard will be implemented in Phase 8. All REST ingestion and retrieval endpoints are operational.')">
                    Documents
                </button>
            </div>

            <!-- 2. Ask AI -->
            <div class="card">
                <div>
                    <span class="card-icon">🤖</span>
                    <h2 class="card-title">Ask AI</h2>
                    <p class="card-desc">Ask questions about institutional guidelines across English, Hindi, Kannada, Telugu, and Romanized queries with strict citation grounding.</p>
                </div>
                <button class="btn" onclick="showFeatureModal('Ask AI Assistant', 'The interactive multilingual chat interface with live citation viewer is scheduled for Phase 8. The backend RAG coordinator is fully active and accepting queries.')">
                    Ask AI
                </button>
            </div>

            <!-- 3. Analytics -->
            <div class="card">
                <div>
                    <span class="card-icon">📊</span>
                    <h2 class="card-title">Analytics</h2>
                    <p class="card-desc">View privacy-preserving query access patterns, language distributions, and PySpark big data analytics summaries.</p>
                </div>
                <button class="btn" onclick="showFeatureModal('Analytics Dashboard', 'The interactive visual analytics dashboard with charts is scheduled for Phase 8. Precomputed PySpark analytics are currently available via REST APIs.')">
                    Analytics
                </button>
            </div>
        </div>

        <!-- Status and Developer Tools -->
        <div class="bottom-section">
            <!-- System Status -->
            <div class="section-card">
                <div class="section-header">
                    <span>⚡</span> System Status
                </div>
                <div class="status-grid">
                    <div class="status-item">
                        <span class="status-label">Backend</span>
                        <span class="status-value" id="status-backend">
                            <span class="status-dot"></span> Online
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Database</span>
                        <span class="status-value" id="status-db">
                            <span class="status-dot"></span> Connected
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">AI/RAG</span>
                        <span class="status-value" id="status-rag">
                            <span class="status-dot"></span> Ready
                        </span>
                    </div>
                    <div class="status-item">
                        <span class="status-label">Analytics</span>
                        <span class="status-value" id="status-analytics">
                            <span class="status-dot"></span> Available
                        </span>
                    </div>
                </div>
            </div>

            <!-- Developer Tools -->
            <div class="section-card">
                <div class="section-header">
                    <span>🛠️</span> Developer Tools
                </div>
                <div class="dev-links">
                    <a href="/docs" class="dev-link-btn">
                        <span>📖 Interactive Swagger UI</span>
                        <span class="badge">/docs</span>
                    </a>
                    <a href="/redoc" class="dev-link-btn">
                        <span>📑 API Reference (ReDoc)</span>
                        <span class="badge">/redoc</span>
                    </a>
                    <a href="/health" target="_blank" class="dev-link-btn">
                        <span>🩺 Health Check JSON</span>
                        <span class="badge">/health</span>
                    </a>
                    <a href="/api/v1/analytics/summary" target="_blank" class="dev-link-btn">
                        <span>📈 Analytics Summary JSON</span>
                        <span class="badge">/api/v1/analytics/summary</span>
                    </a>
                </div>
            </div>
        </div>

        <footer>
            Bangalore Institute of Technology • Multilingual AI Document Assistant • Phase 0–7 Verified
        </footer>
    </div>

    <!-- Modal Dialog -->
    <div class="modal-overlay" id="featureModal" onclick="closeFeatureModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-icon" id="modalIcon">🚀</div>
            <h3 class="modal-title" id="modalTitle">Feature Preview</h3>
            <p class="modal-desc" id="modalDesc">Detailed description goes here.</p>
            <div style="display: flex; gap: 0.75rem;">
                <button class="btn btn-outline" onclick="closeFeatureModal()">Close</button>
                <a href="/docs" class="btn">Explore API Docs</a>
            </div>
        </div>
    </div>

    <script>
        function showFeatureModal(title, desc) {
            document.getElementById('modalTitle').innerText = title;
            document.getElementById('modalDesc').innerText = desc;
            document.getElementById('featureModal').style.display = 'flex';
        }

        function closeFeatureModal() {
            document.getElementById('featureModal').style.display = 'none';
        }

        // Fetch live system health status
        async function fetchSystemHealth() {
            try {
                const res = await fetch('/health');
                if (res.ok) {
                    const data = await res.json();
                    if (data.status === 'ok') {
                        document.getElementById('status-backend').innerHTML = '<span class="status-dot"></span> Online';
                    }
                    if (data.database_status === 'connected') {
                        document.getElementById('status-db').innerHTML = '<span class="status-dot"></span> Connected';
                    }
                    if (data.vector_store_configured) {
                        document.getElementById('status-rag').innerHTML = '<span class="status-dot"></span> Ready';
                    }
                }
            } catch (err) {
                console.warn('Health check fetch failed:', err);
            }

            try {
                const aRes = await fetch('/api/v1/analytics/health');
                if (aRes.ok) {
                    const aData = await aRes.json();
                    if (aData.status === 'healthy' || aData.analytics_precomputed) {
                        document.getElementById('status-analytics').innerHTML = '<span class="status-dot"></span> Available';
                    }
                }
            } catch (err) {
                console.warn('Analytics health fetch failed:', err);
            }
        }

        window.addEventListener('DOMContentLoaded', fetchSystemHealth);
    </script>
</body>
</html>
"""
