# Phase 4 — Model Selection and Runtime Environment

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Embedding Model:** `intfloat/multilingual-e5-small`  
**Embedding Dimension:** 384  
**Runtime:** CPU-first (Apple Silicon macOS arm64)

---

## 1. Embedding Model Selection Rationale

The project standardizes on `intfloat/multilingual-e5-small` based on the following criteria:

1. **Native Multilingual Coverage:** Pretrained across 94+ languages with extensive coverage for Indic scripts (Hindi, Kannada, Telugu) and Latin/English.
2. **Compact Dimension (384):** Produces 384-dimensional dense vectors, significantly reducing memory and disk footprints compared to 768-dim or 1024-dim models while retaining high retrieval quality.
3. **Sequence Length (512 tokens):** Comfortably encompasses the Phase 3 chunk size target of 600 characters (~120–150 tokens), avoiding truncation of meaningful institutional text.
4. **CPU Efficiency:** Capable of running fast local inference on development laptops without requiring dedicated GPU or CUDA runtimes.

---

## 2. Input Prefixing Requirements

As per the E5 model specification, distinct task prefixes are required to optimize retrieval geometry in embedding space:

- **Document Passages (Indexing):** Must be prefixed with `passage: `
  - Example: `passage: Autonomous Academic Regulations 2024-2025...`
- **Retrieval Queries (Searching):** Must be prefixed with `query: `
  - Example: `query: What is the minimum attendance requirement?`

The `SentenceTransformerEmbeddingProvider` applies these prefixes automatically based on whether `embed_documents` or `embed_query` is invoked.

---

## 3. Runtime & Hardware Configuration

- **Device:** `cpu` (Default).
- **Batch Size:** `8` (Configurable via `EMBEDDING_BATCH_SIZE`).
- **Normalization:** `True` (Embeddings are normalized to unit L2 length, making cosine similarity mathematically equivalent to the inner dot product).
- **Cache Location:** Standard HuggingFace cache directory (or custom path via `EMBEDDING_MODEL_CACHE_DIR`).
