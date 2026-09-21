"""
In-Memory Unicode Lexical (BM25) Retriever Module
"""

import json
import math
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from app.core.config import PROJECT_ROOT, settings
from app.core.logging import logger
from app.services.retrieval.constants import METHOD_LEXICAL
from app.services.retrieval.exceptions import LexicalRetrievalError
from app.services.retrieval.models import CandidateChunk, ProcessedQuery, RetrievalFilter

# Tokenizer pattern preserving Unicode alphanumeric words and Indic scripts (Devanagari, Kannada, Telugu)
_TOKEN_PATTERN = re.compile(r"[\w\u0900-\u0D7F]+", re.UNICODE)


def tokenize(text: str) -> List[str]:
    """Tokenizes text into Unicode alphanumeric tokens, lowercased."""
    if not text:
        return []
    return [t.lower() for t in _TOKEN_PATTERN.findall(text) if len(t) > 0]


class InMemoryBM25Index:
    """
    Lightweight, in-memory BM25 index built directly from Phase 3 chunk artifacts.
    Requires no external dependencies or background services.
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.corpus: List[Dict] = []
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.term_freqs_list: List[Dict[str, int]] = []
        self.idf: Dict[str, float] = {}
        self.num_docs: int = 0

    def index_chunks(self, chunks: List[Dict]) -> None:
        """Indexes a list of raw or serialized chunk dictionaries."""
        self.corpus = chunks
        self.num_docs = len(chunks)
        self.doc_lengths = []
        self.doc_freqs = {}
        self.term_freqs_list = []

        total_len = 0
        for chunk in chunks:
            text = chunk.get("text_content") or chunk.get("chunk_text") or ""
            tokens = tokenize(text)
            length = len(tokens)
            self.doc_lengths.append(length)
            total_len += length

            tf: Dict[str, int] = {}
            for token in tokens:
                tf[token] = tf.get(token, 0) + 1
            self.term_freqs_list.append(tf)

            for token in set(tokens):
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

        self.avg_doc_len = total_len / max(1, self.num_docs)

        # Precompute Robertson-Spärck Jones IDF with smoothing
        self.idf = {}
        for token, df in self.doc_freqs.items():
            self.idf[token] = math.log(1.0 + (self.num_docs - df + 0.5) / (df + 0.5))

    def score(self, query_tokens: List[str], doc_idx: int) -> float:
        """Computes BM25 score for a given document index."""
        if self.num_docs == 0 or doc_idx >= self.num_docs:
            return 0.0

        doc_len = self.doc_lengths[doc_idx]
        tf_dict = self.term_freqs_list[doc_idx]
        score = 0.0

        len_norm = 1.0 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len))

        for q_token in query_tokens:
            if q_token not in tf_dict:
                continue
            tf = tf_dict[q_token]
            idf = self.idf.get(q_token, 0.0)
            numerator = tf * (self.k1 + 1.0)
            denominator = tf + self.k1 * len_norm
            score += idf * (numerator / max(1e-6, denominator))

        return score


class LexicalRetriever:
    """
    Retrieves candidates using in-memory BM25 scoring over chunk artifacts.
    """

    def __init__(self, processed_dir: Optional[str] = None):
        self.processed_dir = Path(processed_dir or (PROJECT_ROOT / "data" / "processed"))
        self.index = InMemoryBM25Index()
        self._load_and_build_index()

    def _load_and_build_index(self) -> None:
        """Loads all `*_chunks.json` from data/processed and builds the BM25 index."""
        all_chunks: List[Dict] = []
        if self.processed_dir.exists():
            for chunk_file in sorted(self.processed_dir.glob("*_chunks.json")):
                try:
                    with open(chunk_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        chunks = data.get("chunks", [])
                        all_chunks.extend(chunks)
                except Exception as e:
                    logger.warning(f"Could not load chunk file {chunk_file}: {e}")

        self.index.index_chunks(all_chunks)
        logger.info(f"LexicalRetriever initialized with {len(all_chunks)} chunks.")

    def reload(self, chunks: Optional[List[Dict]] = None) -> None:
        """Manually reloads index with provided chunks or from disk."""
        if chunks is not None:
            self.index.index_chunks(chunks)
        else:
            self._load_and_build_index()

    def retrieve(
        self,
        query: ProcessedQuery,
        top_k: int = 12,
        filters: Optional[RetrievalFilter] = None,
        min_score: float = 0.0,
    ) -> List[CandidateChunk]:
        """
        Performs BM25 lexical search over indexed chunks.
        """
        if top_k <= 0 or self.index.num_docs == 0:
            return []

        try:
            raw_tokens = tokenize(query.normalized_query)
            if not raw_tokens:
                return []
            _lex_stopwords = {
                'what', 'is', 'the', 'in', 'for', 'to', 'of', 'and', 'a', 'an', 'on', 'are',
                'how', 'do', 'does', 'explain', 'about', 'which', 'where', 'can', 'be',
                'tell', 'me', 'used', 'with', 'from', 'at', 'by', 'use', 'using', 'mentioned'
            }
            info_tokens = [t for t in raw_tokens if t not in _lex_stopwords]
            tokens = info_tokens if info_tokens else raw_tokens

            raw_scores: List[tuple[int, float]] = []
            max_raw = 0.0

            for idx, chunk in enumerate(self.index.corpus):
                # Apply filters if specified
                if filters:
                    if filters.doc_id and chunk.get("doc_id") != filters.doc_id:
                        continue
                    if filters.category and chunk.get("category") != filters.category:
                        continue
                    if filters.language and chunk.get("language") != filters.language:
                        continue
                    if filters.script and chunk.get("script") != filters.script:
                        continue
                    if filters.page_number is not None and chunk.get("page_number") != filters.page_number:
                        continue
                    if filters.filename and chunk.get("filename") != filters.filename:
                        continue

                s = self.index.score(tokens, idx)
                if s > 0.0:
                    raw_scores.append((idx, s))
                    if s > max_raw:
                        max_raw = s

            if not raw_scores:
                return []

            # Sort descending by raw BM25 score
            raw_scores.sort(key=lambda x: x[1], reverse=True)

            candidates: List[CandidateChunk] = []
            for rank_idx, (idx, raw_s) in enumerate(raw_scores[:top_k], start=1):
                # Normalized lexical score in [0.0, 1.0]
                norm_score = raw_s / max_raw if max_raw > 0 else 0.0
                norm_score = max(0.0, min(1.0, norm_score))

                if norm_score < min_score:
                    continue

                chunk = self.index.corpus[idx]
                text = chunk.get("text_content") or chunk.get("chunk_text") or ""
                
                candidate = CandidateChunk(
                    chunk_id=str(chunk.get("chunk_id", f"chunk_{idx}")),
                    doc_id=str(chunk.get("doc_id", "")),
                    text_content=text,
                    filename=str(chunk.get("filename", "")),
                    category=str(chunk.get("category", "general")),
                    language=str(chunk.get("language", "und")),
                    script=str(chunk.get("script", "Unknown")),
                    page_number=int(chunk.get("page_number", 1)),
                    section_title=str(chunk.get("section_title", "")),
                    heading_level=int(chunk.get("heading_level", 0)),
                    source_start_offset=int(chunk.get("source_start_offset", 0)),
                    source_end_offset=int(chunk.get("source_end_offset", 0)),
                    file_hash_sha256=str(chunk.get("file_hash_sha256", "")),
                    lexical_score=round(norm_score, 4),
                    retrieval_methods=[METHOD_LEXICAL],
                    rank=rank_idx,
                )
                candidates.append(candidate)

            return candidates

        except Exception as e:
            logger.error(f"Lexical retrieval failed: {str(e)}")
            raise LexicalRetrievalError(f"Lexical retrieval failed: {str(e)}") from e
