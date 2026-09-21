# Phase 4 — Embedding Data Contract

**Project:** Multilingual AI Document Assistant with Big Data Analytics  
**Component:** `app.services.embeddings.models.EmbeddedChunk`

---

## 1. Input Contract (from Phase 3)

The embedding pipeline strictly consumes the `DocumentChunk` records from canonical Phase 3 artifacts (`data/processed/{doc_id}_chunks.json`).

The input text passed to the embedding provider is:
$$\text{text} = \text{DocumentChunk.text\_content}$$

No metadata strings, raw file paths, or JSON tags are concatenated into `text_content` before embedding, ensuring pure semantic representations.

---

## 2. Output `EmbeddedChunk` Schema

Every generated `EmbeddedChunk` combines the complete 20-field Phase 3 provenance record with 6 embedding-specific attributes:

| # | Field Name | Type | Description | Example |
| :--- | :--- | :--- | :--- | :--- |
| 1–20 | *(Provenance Fields)* | *Various* | Identical to Phase 3 `DocumentChunk` | `chunk_id`, `doc_id`, `file_hash_sha256`, `page_number`, `section_title`, `text_content`, offsets, etc. |
| 21 | `embedding` | `List[float]` | 384-element float vector | `[0.021, -0.043, ..., 0.089]` |
| 22 | `embedding_model_name` | `str` | Name of model | `"intfloat/multilingual-e5-small"` |
| 23 | `embedding_dimension` | `int` | Vector length | `384` |
| 24 | `embedding_device` | `str` | Hardware device | `"cpu"` |
| 25 | `embedding_normalized` | `bool` | L2 normalization status | `True` |
| 26 | `vector_index_version` | `int` | Index schema version | `1` |

---

## 3. Numerical Integrity Invariants

1. **Dimensionality:** $\forall v \in \text{embeddings}, \text{len}(v) = 384$.
2. **Finiteness:** $\forall x \in v, x \notin \{\text{NaN}, +\infty, -\infty\}$.
3. **Unit Norm:** When `normalize=True`, $\|v\|_2 = \sqrt{\sum_{i=1}^{384} v_i^2} \approx 1.0 \pm 10^{-5}$.
