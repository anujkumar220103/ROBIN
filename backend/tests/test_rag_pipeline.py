# Tests for the complete RAG pipeline — retrieval se answer generation tak.

import uuid
import pytest
from unittest.mock import patch, MagicMock

from app.rag.pipeline import run_rag_pipeline
from app.schemas.chat import ConversationMessage


def _make_chunk(similarity=0.8, text="Employees receive 18 days of annual leave."):
    doc_id = uuid.uuid4()
    return {
        "document_id": doc_id,
        "filename": "policy.pdf",
        "page_number": 3,
        "chunk_id": str(uuid.uuid4()),
        "text": text,
        "distance": 1 - similarity,
        "similarity": similarity,
    }


def _mock_provider_result(answer_text: str):
    return {
        "answer_text": answer_text,
        "provider": "gemini",
        "model": "gemini-2.0-flash",
        "fallback_used": False,
        "latency_ms": 500,
    }


class TestPipelineWithMocks:
    def setup_method(self):
        self.db = MagicMock()
        self.company_id = uuid.uuid4()

    def test_empty_knowledge_base_returns_insufficient(self):
        with patch("app.rag.pipeline.search_company_knowledge", return_value=[]):
            result = run_rag_pipeline(self.db, self.company_id, "What is the leave policy?")
        assert result["status"] == "insufficient_context"
        assert result["sources"] == []

    def test_low_similarity_returns_insufficient(self):
        # Similarity 0.1 is below default threshold 0.35.
        low_chunks = [_make_chunk(similarity=0.1)]
        with patch("app.rag.pipeline.search_company_knowledge", return_value=low_chunks):
            result = run_rag_pipeline(self.db, self.company_id, "What is the leave policy?")
        assert result["status"] == "insufficient_context"

    def test_successful_grounded_answer(self):
        chunks = [_make_chunk(similarity=0.85)]
        llm_json = '{"answer": "Employees receive 18 days of annual leave. [S1]", "source_ids": ["S1"], "insufficient_context": false}'
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", return_value=_mock_provider_result(llm_json)):
                result = run_rag_pipeline(self.db, self.company_id, "What is the leave policy?")
        assert result["status"] == "answered"
        assert len(result["sources"]) == 1
        assert result["sources"][0]["filename"] == "policy.pdf"

    def test_provider_error_returns_provider_error_status(self):
        chunks = [_make_chunk(similarity=0.85)]
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", side_effect=RuntimeError("all providers failed")):
                result = run_rag_pipeline(self.db, self.company_id, "What is the leave policy?")
        assert result["status"] == "provider_error"
        assert result["sources"] == []

    def test_empty_question_returns_invalid_input(self):
        result = run_rag_pipeline(self.db, self.company_id, "")
        assert result["status"] == "invalid_input"

    def test_fallback_metadata_recorded(self):
        chunks = [_make_chunk(similarity=0.85)]
        llm_json = '{"answer": "Policy text [S1]", "source_ids": ["S1"], "insufficient_context": false}'
        fallback_result = {
            "answer_text": llm_json,
            "provider": "groq",
            "model": "llama-3.1-8b-instant",
            "fallback_used": True,
            "latency_ms": 800,
        }
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", return_value=fallback_result):
                result = run_rag_pipeline(self.db, self.company_id, "What is the leave policy?")
        assert result["metadata"]["fallback_used"] is True
        assert result["metadata"]["provider"] == "groq"

    def test_conversation_history_accepted(self):
        history = [
            ConversationMessage(role="user", content="Tell me about benefits."),
            ConversationMessage(role="assistant", content="Which benefit?"),
        ]
        llm_json = '{"answer": "Annual leave is 18 days. [S1]", "source_ids": ["S1"], "insufficient_context": false}'
        chunks = [_make_chunk(similarity=0.85)]
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", return_value=_mock_provider_result(llm_json)):
                result = run_rag_pipeline(
                    self.db, self.company_id, "What about leave?", history=history
                )
        assert result["status"] == "answered"

    def test_retrieved_chunks_count_in_metadata(self):
        chunks = [_make_chunk(similarity=0.85) for _ in range(5)]
        llm_json = '{"answer": "Policy info [S1]", "source_ids": ["S1"], "insufficient_context": false}'
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", return_value=_mock_provider_result(llm_json)):
                result = run_rag_pipeline(self.db, self.company_id, "Tell me about the policy.")
        assert result["metadata"]["retrieved_chunks"] == 5

    def test_insufficient_context_llm_response(self):
        chunks = [_make_chunk(similarity=0.85)]
        llm_json = '{"answer": "I could not find the information.", "source_ids": [], "insufficient_context": true}'
        with patch("app.rag.pipeline.search_company_knowledge", return_value=chunks):
            with patch("app.rag.pipeline.invoke_with_fallback", return_value=_mock_provider_result(llm_json)):
                result = run_rag_pipeline(self.db, self.company_id, "What is the CEO salary?")
        assert result["status"] == "insufficient_context"
        assert result["sources"] == []
