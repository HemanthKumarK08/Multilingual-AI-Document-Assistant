/**
 * Centralized API Service Layer
 * Consumes the Phase 0-7 FastAPI backend without hardcoded credentials or scattered fetch calls.
 */

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

async function request(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  const isFormData = options.body instanceof FormData;

  const config = {
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      'Accept': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      const errorMsg = errorBody.detail || errorBody.message || `HTTP ${response.status}: ${response.statusText}`;
      throw new Error(errorMsg);
    }
    return await response.json();
  } catch (error) {
    console.error(`[API Error] ${config.method || 'GET'} ${url}:`, error.message);
    throw error;
  }
}

export const apiService = {
  // System Health
  async getHealth() {
    return request('/health');
  },

  // Analytics Health & Endpoints
  async getAnalyticsHealth() {
    return request('/api/v1/analytics/health');
  },

  async getAnalyticsSummary() {
    return request('/api/v1/analytics/summary');
  },

  async getAnalyticsVolume() {
    return request('/api/v1/analytics/volume');
  },

  async getAnalyticsLanguages() {
    return request('/api/v1/analytics/languages');
  },

  async getAnalyticsRetrieval() {
    return request('/api/v1/analytics/retrieval');
  },

  async getAnalyticsRag() {
    return request('/api/v1/analytics/rag');
  },

  async getAnalyticsErrors() {
    return request('/api/v1/analytics/errors');
  },

  async getAnalyticsTimeseries() {
    return request('/api/v1/analytics/timeseries');
  },

  // Document Management
  async getDocuments(category = null, activeOnly = true) {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (activeOnly !== null) params.append('active_only', activeOnly);
    const qs = params.toString();
    return request(`/api/v1/documents${qs ? `?${qs}` : ''}`);
  },

  async getDocumentById(docId) {
    return request(`/api/v1/documents/${encodeURIComponent(docId)}`);
  },

  async uploadDocument(file, displayTitle = '', category = 'academic_regulations', version = '1.0', allowReingest = true) {
    const formData = new FormData();
    formData.append('file', file);
    if (displayTitle) formData.append('display_title', displayTitle);
    formData.append('category', category);
    formData.append('version', version);
    formData.append('allow_reingest', allowReingest);

    return request('/api/v1/documents/upload', {
      method: 'POST',
      body: formData,
    });
  },

  async ingestDocument(payload) {
    return request('/api/v1/documents/ingest', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  // Question Answering / RAG
  async submitQuery(queryText, targetLanguage = 'en', category = null) {
    return request('/api/v1/qa/query', {
      method: 'POST',
      body: JSON.stringify({
        query_text: queryText,
        target_language: targetLanguage,
        category: category,
      }),
    });
  },

  // Quality Feedback
  async submitFeedback(queryId, feedback, comment = null) {
    return request('/api/v1/qa/feedback', {
      method: 'POST',
      body: JSON.stringify({
        query_id: queryId,
        feedback: feedback,
        comment: comment,
      }),
    });
  },
};

export default apiService;
