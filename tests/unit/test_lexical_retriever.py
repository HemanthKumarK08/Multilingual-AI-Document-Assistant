"""
Unit Tests for In-Memory BM25 Lexical Retriever (Phase 5)
"""

import pytest
from app.services.retrieval.lexical_retriever import InMemoryBM25Index, LexicalRetriever, tokenize
from app.services.retrieval.models import ProcessedQuery, RetrievalFilter


class TestLexicalRetrieverUnit:
    def test_unicode_tokenization(self):
        text = "Hello, world! उपस्थिति ಮತ್ತು హాజరు 123"
        tokens = tokenize(text)
        assert "hello" in tokens
        assert "world" in tokens
        assert "उपस्थिति" in tokens
        assert "ಮತ್ತು" in tokens
        assert "హాజరు" in tokens
        assert "123" in tokens

    def test_in_memory_bm25_scoring(self):
        index = InMemoryBM25Index()
        docs = [
            {"chunk_id": "c1", "text_content": "The attendance requirement is 75% for all courses."},
            {"chunk_id": "c2", "text_content": "Hostel fee payment deadline is the 10th of every month."},
            {"chunk_id": "c3", "text_content": "Attendance condonation is available only above 65%."},
        ]
        index.index_chunks(docs)

        query_tokens = tokenize("attendance requirement")
        score_c1 = index.score(query_tokens, 0)
        score_c2 = index.score(query_tokens, 1)
        score_c3 = index.score(query_tokens, 2)

        assert score_c1 > score_c2
        assert score_c1 > score_c3
        assert score_c2 == 0.0

    def test_lexical_retriever_reload_and_query(self):
        retriever = LexicalRetriever(processed_dir="/non/existent/dir")
        test_chunks = [
            {
                "chunk_id": "c_attn_1",
                "doc_id": "doc_attn",
                "filename": "attn.pdf",
                "category": "academic",
                "text_content": "Minimum attendance requirement is 75 percent.",
                "page_number": 1,
            },
            {
                "chunk_id": "c_hostel_1",
                "doc_id": "doc_hostel",
                "filename": "hostel.pdf",
                "category": "hostel",
                "text_content": "Hostel mess charges are payable semesterly.",
                "page_number": 1,
            }
        ]
        retriever.reload(chunks=test_chunks)

        pq = ProcessedQuery(raw_query="attendance percent", normalized_query="attendance percent")
        results = retriever.retrieve(pq, top_k=2)

        assert len(results) == 1
        assert results[0].chunk_id == "c_attn_1"
        assert results[0].lexical_score > 0.0
        assert results[0].retrieval_methods == ["lexical"]

    def test_lexical_retriever_filter(self):
        retriever = LexicalRetriever(processed_dir="/non/existent/dir")
        test_chunks = [
            {"chunk_id": "c1", "doc_id": "d1", "category": "academic", "text_content": "Policy 1"},
            {"chunk_id": "c2", "doc_id": "d2", "category": "hostel", "text_content": "Policy 2"},
        ]
        retriever.reload(chunks=test_chunks)

        pq = ProcessedQuery(raw_query="policy", normalized_query="policy")
        filt = RetrievalFilter(category="hostel")
        results = retriever.retrieve(pq, filters=filt)

        assert len(results) == 1
        assert results[0].chunk_id == "c2"
