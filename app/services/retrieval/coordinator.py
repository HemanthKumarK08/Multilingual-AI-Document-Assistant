"""
Simplified Retrieval Coordinator (Reference RAG Architecture)

Pipeline:
  1. Embed current query (single embedding, no variants)
  2. ChromaDB vector search (top CANDIDATES)
  3. BM25 search over cached index (top CANDIDATES)
  4. Reciprocal Rank Fusion (k=60) to fuse both lists
  5. Return top-K results

This replaces the over-engineered multi-query-variant + cross-encoder pipeline.
"""
from __future__ import annotations

import re
import time
from functools import lru_cache
from typing import Dict, List, Optional, Tuple

from app.core.config import settings
from app.core.logging import logger
from app.services.retrieval.models import (
    CandidateChunk,
    ProcessedQuery,
    RetrievalFilter,
    RetrievalResult,
)

# ---------------------------------------------------------------------------
# Configuration constants (from reference project)
# ---------------------------------------------------------------------------
RETRIEVAL_CANDIDATES = 20   # candidate pool before RRF fusion
RETRIEVAL_TOP_K = 5         # final evidence chunks
RRF_K = 60.0               # RRF smoothing constant

# Tokenizer for BM25 (Unicode-aware, preserves Indic scripts)
_TOKEN_RE = re.compile(r"[\w\u0900-\u0D7F]+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text) if t]


# ---------------------------------------------------------------------------
# BM25 Index (cached per collection snapshot size, built from ChromaDB)
# ---------------------------------------------------------------------------

def _get_collection():
    """Lazy import to avoid circular dependency at module load."""
    from app.services.vector_store.chroma_client import get_persistent_chroma_client
    from app.services.vector_store.collection import get_or_create_collection
    from app.services.vector_store.models import VectorStoreConfig

    config = VectorStoreConfig(
        persist_directory=settings.VECTOR_STORE_PERSIST_DIRECTORY,
        collection_name=settings.VECTOR_STORE_COLLECTION_NAME,
        distance_metric=settings.VECTOR_STORE_DISTANCE_METRIC,
        index_version=settings.VECTOR_INDEX_VERSION,
    )
    client = get_persistent_chroma_client(config.persist_directory)
    return get_or_create_collection(client=client, config=config,
                                    embedding_model_name=settings.EMBEDDING_MODEL_NAME,
                                    dimension=settings.EMBEDDING_DIMENSION)


_bm25_revision: int = 0


def clear_bm25_cache() -> None:
    """Authoritative cache invalidation for the active BM25 lexical index."""
    global _bm25_revision
    _bm25_revision += 1
    _get_bm25_index.cache_clear()
    logger.info(f"Active BM25 cache cleared (revision={_bm25_revision}).")


def _collection_snapshot() -> Tuple[List[str], List[str], List[dict]]:
    """Returns strictly aligned (ids, documents, metadatas) from a single ChromaDB call."""
    col = _get_collection()
    data = col.get(include=["documents", "metadatas"])
    ids = data.get("ids") or []
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    return ids, docs, metas


@lru_cache(maxsize=1)
def _get_bm25_index(revision: int, id_hash: str):
    """
    BM25 index cached by:
    1. revision: incremented on explicit clear_bm25_cache() calls.
    2. id_hash: hash of all chunk IDs in collection to detect changes with equal chunk count.
    Returns: (BM25Okapi, ids, docs, metas)
    """
    try:
        from rank_bm25 import BM25Okapi
    except ImportError:
        logger.warning("rank_bm25 not installed; BM25 disabled. Install: pip install rank-bm25")
        return None, [], [], []

    ids, docs, metas = _collection_snapshot()
    if not docs:
        return None, [], [], []
    corpus = [_tokenize(d) for d in docs]
    return BM25Okapi(corpus), ids, docs, metas


# Backward-compatible alias
def _bm25_for_count(count: int):
    """Legacy alias that forwards to _get_bm25_index."""
    return _get_bm25_index(_bm25_revision, str(count))


def _bm25_search(text: str, top_k: int, filters: Optional[RetrievalFilter]) -> Dict[str, float]:
    """Returns {chunk_id: normalized_bm25_score}."""
    if not text.strip():
        return {}

    col = _get_collection()
    try:
        total = col.count()
    except Exception:
        total = 0
    if total == 0:
        return {}

    import hashlib
    data_ids = col.get(include=[]).get("ids") or []
    if not data_ids:
        return {}
    id_hash = hashlib.sha256(",".join(data_ids).encode("utf-8")).hexdigest()

    bm25, ids, docs, metas = _get_bm25_index(_bm25_revision, id_hash)
    if bm25 is None or not docs:
        return {}

    tokens = _tokenize(text)
    raw_scores = bm25.get_scores(tokens)
    order = sorted(range(len(docs)), key=lambda i: raw_scores[i], reverse=True)[: top_k * 3]

    max_score = max((raw_scores[i] for i in order if raw_scores[i] > 0), default=1.0)
    if max_score <= 0:
        max_score = 1.0

    out: Dict[str, float] = {}
    for i in order:
        if raw_scores[i] <= 0:
            continue
        if i >= len(ids):
            continue
        chunk_id = ids[i]
        if filters and metas and i < len(metas):
            meta = metas[i]
            if filters.category and meta.get("category") != filters.category:
                continue
            if filters.doc_id and meta.get("doc_id") != filters.doc_id:
                continue
        out[chunk_id] = float(raw_scores[i]) / max_score
        if len(out) >= top_k:
            break
    return out



def _rrf_fuse(rankings: List[Dict[str, float]], k: float = RRF_K) -> Dict[str, float]:
    """Reciprocal Rank Fusion: score = Σ 1/(k + rank_i). Input: [{id: score}]."""
    fused: Dict[str, float] = {}
    for ranking in rankings:
        for rank, chunk_id in enumerate(
            sorted(ranking, key=lambda i: ranking[i], reverse=True), start=1
        ):
            fused[chunk_id] = fused.get(chunk_id, 0.0) + 1.0 / (k + rank)
    return fused


# ---------------------------------------------------------------------------
# Embedding (reuses the existing SentenceTransformer provider)
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def _get_embedding_provider():
    from app.services.embeddings.sentence_transformer import SentenceTransformerEmbeddingProvider
    return SentenceTransformerEmbeddingProvider()


def _expand_indic_query(query_text: str) -> str:
    """If query contains Indic keywords from dictionary, append English equivalents."""
    try:
        from app.services.retrieval.query_expansion import _INDIC_TERM_TRANSLATIONS
        tokens = re.findall(r"[\w\u0900-\u0D7F]+", query_text.lower())
        exp = []
        for t in tokens:
            if t in _INDIC_TERM_TRANSLATIONS:
                exp.extend(_INDIC_TERM_TRANSLATIONS[t])
        if exp:
            seen = set()
            unique_exp = [x for x in exp if not (x in seen or seen.add(x))]
            return f"{query_text} {' '.join(unique_exp)}"
    except Exception:
        pass
    return query_text


# ---------------------------------------------------------------------------
# Main retrieval function
# ---------------------------------------------------------------------------

def simple_retrieve(
    query_text: str,
    filters: Optional[RetrievalFilter] = None,
    top_k: int = RETRIEVAL_TOP_K,
    n_candidates: int = RETRIEVAL_CANDIDATES,
) -> List[CandidateChunk]:
    """
    Single-pass hybrid retrieval:
      1. Expand Indic tokens if needed
      2. Embed query
      3. ChromaDB vector search (n_candidates)
      4. BM25 search (n_candidates)
      5. RRF fusion
      6. Return top_k CandidateChunk objects
    """
    from app.services.vector_store.metadata import deserialize_chunk_metadata

    emb = _get_embedding_provider()
    search_query = _expand_indic_query(query_text)

    # 1. Query embedding
    query_vector = emb.embed_query(search_query)
    if hasattr(query_vector, "tolist"):
        query_vector = query_vector.tolist()

    col = _get_collection()
    total_count = col.count()
    if total_count == 0:
        return []

    actual_n = min(n_candidates, total_count)

    # Build where clause for ChromaDB
    where_clause = None
    if filters:
        where_clause = filters.to_chroma_where()

    # 2. ChromaDB vector search
    try:
        kwargs = {
            "query_embeddings": [query_vector],
            "n_results": actual_n,
            "include": ["documents", "metadatas", "distances"],
        }
        if where_clause:
            kwargs["where"] = where_clause
        res = col.query(**kwargs)
    except RuntimeError as e:
        logger.warning(f"ChromaDB query error, attempting brute force: {e}")
        res = _brute_force_query(col, query_vector, actual_n, where_clause)

    ids = (res.get("ids") or [[]])[0]
    docs = (res.get("documents") or [[]])[0]
    metas = (res.get("metadatas") or [[]])[0]
    dists = (res.get("distances") or [[]])[0]

    # Map chunk_id -> CandidateChunk for vector results
    vec_ranking: Dict[str, float] = {}
    chunk_map: Dict[str, CandidateChunk] = {}

    for chunk_id, doc, raw_meta, dist in zip(ids, docs, metas, dists):
        score = round(max(0.0, 1.0 - float(dist)), 4)
        meta = deserialize_chunk_metadata(raw_meta)
        vec_ranking[chunk_id] = score
        chunk_map[chunk_id] = CandidateChunk(
            chunk_id=str(chunk_id),
            doc_id=str(meta.get("doc_id", "")),
            text_content=str(doc or ""),
            filename=str(meta.get("filename", "")),
            category=str(meta.get("category", "general")),
            language=str(meta.get("language", "und")),
            script=str(meta.get("script", "Unknown")),
            page_number=int(meta.get("page_number", 1)),
            section_title=str(meta.get("section_title", "")),
            heading_level=int(meta.get("heading_level", 0)),
            source_start_offset=int(meta.get("source_start_offset", 0)),
            source_end_offset=int(meta.get("source_end_offset", 0)),
            file_hash_sha256=str(meta.get("file_hash_sha256", "")),
            dense_score=score,
            retrieval_methods=["dense"],
        )

    # 3. BM25 search
    bm25_ranking = _bm25_search(search_query, n_candidates, filters)

    # 4. RRF fusion
    fused = _rrf_fuse([vec_ranking, bm25_ranking])

    # 5. Sort by RRF score, take top_k
    ordered_ids = sorted(fused, key=lambda i: fused[i], reverse=True)

    # Hydrate any missing BM25 chunks not in ChromaDB top-N
    missing_ids = [cid for cid in ordered_ids[:top_k] if cid not in chunk_map]
    if missing_ids:
        try:
            missing_data = col.get(ids=missing_ids, include=["documents", "metadatas"])
            m_ids = missing_data.get("ids") or []
            m_docs = missing_data.get("documents") or []
            m_metas = missing_data.get("metadatas") or []
            for m_id, m_doc, m_meta in zip(m_ids, m_docs, m_metas):
                meta = deserialize_chunk_metadata(m_meta)
                chunk_map[m_id] = CandidateChunk(
                    chunk_id=str(m_id),
                    doc_id=str(meta.get("doc_id", "")),
                    text_content=str(m_doc or ""),
                    filename=str(meta.get("filename", "")),
                    category=str(meta.get("category", "general")),
                    language=str(meta.get("language", "und")),
                    script=str(meta.get("script", "Unknown")),
                    page_number=int(meta.get("page_number", 1)),
                    section_title=str(meta.get("section_title", "")),
                    heading_level=int(meta.get("heading_level", 0)),
                    source_start_offset=int(meta.get("source_start_offset", 0)),
                    source_end_offset=int(meta.get("source_end_offset", 0)),
                    file_hash_sha256=str(meta.get("file_hash_sha256", "")),
                    dense_score=0.0,
                    retrieval_methods=["bm25"],
                )
        except Exception as e:
            logger.warning(f"Error fetching missing BM25 chunks: {e}")

    results: List[CandidateChunk] = []
    for rank_idx, cid in enumerate(ordered_ids[:top_k], start=1):
        if cid in chunk_map:
            cand = chunk_map[cid].model_copy(deep=True)
            cand.rrf_score = round(fused[cid], 6)
            cand.hybrid_score = round(fused[cid], 6)
            methods = []
            if cid in vec_ranking:
                methods.append("dense")
            if cid in bm25_ranking:
                cand.lexical_score = round(bm25_ranking[cid], 4)
                methods.append("bm25")
            cand.retrieval_methods = methods or ["dense"]
            cand.rank = rank_idx
            results.append(cand)

    return results


def _brute_force_query(col, query_vector, n_results: int, where_clause) -> dict:
    """Fallback brute-force cosine similarity when HNSW index is damaged."""
    import numpy as np

    kwargs = {"include": ["embeddings", "documents", "metadatas"]}
    if where_clause:
        kwargs["where"] = where_clause
    data = col.get(**kwargs)

    embeddings = data.get("embeddings") or []
    docs = data.get("documents") or []
    metas = data.get("metadatas") or []
    ids = data.get("ids") or []

    if not embeddings:
        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    q = np.array(query_vector, dtype=np.float32)
    matrix = np.array(embeddings, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1) * np.linalg.norm(q)
    norms[norms == 0] = 1e-9
    similarities = (matrix @ q) / norms
    order = np.argsort(-similarities)[:n_results]

    return {
        "ids": [[ids[i] for i in order]],
        "documents": [[docs[i] for i in order]],
        "metadatas": [[metas[i] for i in order]],
        "distances": [[float(1.0 - similarities[i]) for i in order]],
    }


# ---------------------------------------------------------------------------
# RetrievalCoordinator: thin wrapper so existing API code keeps working
# ---------------------------------------------------------------------------

class RetrievalCoordinator:
    """
    Simplified coordinator wrapping simple_retrieve().
    Replaces the multi-query-expansion coordinator.
    The `dense_retriever` and `lexical_retriever` attributes are kept for
    compatibility with the main.py pre-warm code.
    """

    def __init__(self, dense_retriever=None, lexical_retriever=None):
        # Keep references so main.py pre-warming still works
        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever

    def retrieve(
        self,
        raw_query: str,
        language: Optional[str] = None,
        target_language: Optional[str] = None,
        filters: Optional[RetrievalFilter] = None,
        dense_top_k: Optional[int] = None,
        lexical_top_k: Optional[int] = None,
        final_top_k: Optional[int] = None,
        dense_weight: Optional[float] = None,
        lexical_weight: Optional[float] = None,
        enable_reranking: Optional[bool] = None,
        enable_query_expansion: Optional[bool] = None,
        conversation_history=None,
    ) -> RetrievalResult:
        """Single-pass hybrid retrieval. All advanced options are ignored."""
        start_time = time.perf_counter()

        top_k = final_top_k or RETRIEVAL_TOP_K
        n_cands = RETRIEVAL_CANDIDATES

        from app.services.retrieval.multilingual_variants import generate_retrieval_variants

        variants = generate_retrieval_variants(raw_query)
        logger.info(f"Multilingual retrieval query variants ({len(variants)}): {variants}")

        try:
            if len(variants) <= 1:
                candidates = simple_retrieve(
                    query_text=raw_query,
                    filters=filters,
                    top_k=top_k,
                    n_candidates=n_cands,
                )
            else:
                variant_candidates = []
                for v in variants:
                    v_cands = simple_retrieve(
                        query_text=v,
                        filters=filters,
                        top_k=n_cands,
                        n_candidates=n_cands,
                    )
                    variant_candidates.append((v, v_cands))

                # Multi-variant RRF Fusion (k=60, Section D: preserve strongest rank)
                best_ranks: Dict[str, int] = {}
                fused_scores: Dict[str, float] = {}
                chunk_map: Dict[str, CandidateChunk] = {}
                variant_tags: Dict[str, List[str]] = {}

                for v_text, cands in variant_candidates:
                    for rank_idx, c in enumerate(cands, start=1):
                        cid = c.chunk_id
                        if cid not in variant_tags:
                            variant_tags[cid] = []
                        if v_text not in variant_tags[cid]:
                            variant_tags[cid].append(v_text)

                        if cid not in best_ranks or rank_idx < best_ranks[cid]:
                            best_ranks[cid] = rank_idx

                        if cid not in chunk_map:
                            chunk_map[cid] = c.model_copy(deep=True)
                        else:
                            existing = chunk_map[cid]
                            # Preserve strongest dense and lexical scores
                            if (c.dense_score or 0.0) > (existing.dense_score or 0.0):
                                existing.dense_score = c.dense_score
                            if (c.lexical_score or 0.0) > (existing.lexical_score or 0.0):
                                existing.lexical_score = c.lexical_score
                            for m in c.retrieval_methods:
                                if m not in existing.retrieval_methods:
                                    existing.retrieval_methods.append(m)

                # Compute fused RRF score preserving strongest rank across all variants
                # Score = 1.0 / (RRF_K + best_rank) with tiny lexical/dense tie-breaker
                for cid, b_rank in best_ranks.items():
                    rrf_base = 1.0 / (RRF_K + b_rank)
                    lex_tie = float((chunk_map[cid].lexical_score or 0.0) * 1e-4)
                    dense_tie = float((chunk_map[cid].dense_score or 0.0) * 1e-4)
                    fused_scores[cid] = rrf_base + lex_tie + dense_tie

                # Order deduplicated candidates by fused score
                ordered_ids = sorted(fused_scores, key=lambda i: fused_scores[i], reverse=True)

                # Build final candidate list (pool max 20, context top_k=5)
                pool_limit = max(top_k, 20)
                fused_candidates: List[CandidateChunk] = []
                for final_rank, cid in enumerate(ordered_ids[:pool_limit], start=1):
                    cand = chunk_map[cid]
                    cand.rank = final_rank
                    cand.rrf_score = round(1.0 / (RRF_K + best_ranks[cid]), 6)
                    cand.hybrid_score = round(fused_scores[cid], 6)
                    cand.query_variant_sources = variant_tags.get(cid, [])
                    fused_candidates.append(cand)

                candidates = fused_candidates
        except Exception as e:
            logger.error(f"multilingual_retrieve failed: {e}")
            candidates = []

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0

        # Determine script and language
        script = "Latin"
        if re.search(r"[\u0900-\u097F]", raw_query):
            script = "Devanagari"
        elif re.search(r"[\u0C80-\u0CFF]", raw_query):
            script = "Kannada"
        elif re.search(r"[\u0C00-\u0C7F]", raw_query):
            script = "Telugu"
        elif language == "hi":
            script = "Devanagari"
        elif language == "kn":
            script = "Kannada"
        elif language == "te":
            script = "Telugu"

        det_lang = language
        if not det_lang or det_lang in ("und", "auto"):
            if script == "Devanagari":
                det_lang = "hi"
            elif script == "Kannada":
                det_lang = "kn"
            elif script == "Telugu":
                det_lang = "te"
            else:
                det_lang = "en"

        pq = ProcessedQuery(
            raw_query=raw_query,
            normalized_query=raw_query,
            language=det_lang,
            target_language=target_language or det_lang,
            script=script,
            query_intent="FACTUAL",
        )

        return RetrievalResult(
            query=pq,
            candidates=candidates,
            total_candidates_found=len(candidates),
            selected_candidates_count=len(candidates),
            query_variant_count=len(variants),
            latency_ms=round(elapsed_ms, 2),
            filters_applied=filters,
        )
