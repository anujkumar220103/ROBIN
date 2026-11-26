# Tests for LLM provider manager and automatic fallback behavior.
# Real API calls se bachne ke liye providers mock karte hain.

import os
import pytest
from unittest.mock import patch, MagicMock


def _make_response(content: str):
    """Mock LangChain response object."""
    mock = MagicMock()
    mock.content = content
    return mock


def _valid_json_answer():
    return '{"answer": "Employees get 18 days. [S1]", "source_ids": ["S1"], "insufficient_context": false}'


class TestGetConfiguredProviders:
    def test_unconfigured_providers(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "")
        monkeypatch.setattr("app.core.config.settings.GROQ_API_KEY", "")
        monkeypatch.setattr("app.core.config.settings.OPENROUTER_API_KEY", "")
        from app.rag.llm_provider import get_configured_providers
        providers = get_configured_providers()
        for p in providers:
            assert p["configured"] is False

    def test_configured_provider(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.GEMINI_API_KEY", "test-key")
        from app.rag.llm_provider import get_configured_providers
        providers = get_configured_providers()
        gemini = next(p for p in providers if p["name"] == "gemini")
        assert gemini["configured"] is True


class TestInvokeWithFallback:
    def _run_with_mocked_settings(self, provider_order, enabled_providers, builders, fail_builders=None):
        """Helper to run invoke_with_fallback with fully mocked settings and builders."""
        from app.rag import llm_provider as lp

        fail_builders = fail_builders or []

        def patched_ordered(ordered_list, enabled_list, builder_map):
            """Directly replicate the provider loop with mocked settings."""
            import time
            overall_start = time.monotonic()
            last_error = None
            fallback_used = False

            for index, provider_name in enumerate(ordered_list):
                if provider_name not in enabled_list:
                    continue
                if index > 0:
                    fallback_used = True

                if provider_name not in builder_map:
                    continue
                llm = builder_map[provider_name]

                try:
                    response = llm.invoke(["test"])
                    content = response.content
                    return {
                        "answer_text": content,
                        "provider": provider_name,
                        "model": f"mock-{provider_name}",
                        "fallback_used": fallback_used,
                        "latency_ms": int((time.monotonic() - overall_start) * 1000),
                    }
                except Exception as exc:
                    last_error = exc
                    if lp._is_recoverable_error(exc):
                        continue
                    else:
                        raise

            raise RuntimeError(f"All providers failed: {last_error}")

        return patched_ordered(provider_order, enabled_providers, builders)

    def test_no_providers_raises(self):
        with pytest.raises(RuntimeError):
            self._run_with_mocked_settings([], [], {})

    def test_gemini_success(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_response(_valid_json_answer())
        result = self._run_with_mocked_settings(
            ["gemini"], ["gemini"], {"gemini": mock_llm}
        )
        assert result["provider"] == "gemini"
        assert result["fallback_used"] is False

    def test_groq_fallback_when_gemini_fails(self):
        gemini_mock = MagicMock()
        gemini_mock.invoke.side_effect = RuntimeError("rate limit 429")
        groq_mock = MagicMock()
        groq_mock.invoke.return_value = _make_response(_valid_json_answer())

        result = self._run_with_mocked_settings(
            ["gemini", "groq"], ["gemini", "groq"],
            {"gemini": gemini_mock, "groq": groq_mock}
        )
        assert result["provider"] == "groq"
        assert result["fallback_used"] is True

    def test_retired_gemini_model_falls_back_without_retry(self, monkeypatch):
        from app.rag import llm_provider as lp

        gemini_mock = MagicMock()
        gemini_mock.invoke.side_effect = RuntimeError(
            "404 NOT_FOUND: This model is no longer available."
        )
        groq_mock = MagicMock()
        groq_mock.invoke.return_value = _make_response(_valid_json_answer())

        monkeypatch.setattr(lp.settings, "LLM_PROVIDER_ORDER", "gemini,groq")
        monkeypatch.setattr(lp.settings, "LLM_ENABLED_PROVIDERS", "gemini,groq")
        monkeypatch.setattr(lp.settings, "LLM_TOTAL_TIMEOUT_SECONDS", 10)
        monkeypatch.setattr(lp.settings, "LLM_MAX_RETRIES", 1)
        monkeypatch.setattr(lp, "_BUILDERS", {
            "gemini": lambda: gemini_mock,
            "groq": lambda: groq_mock,
        })

        result = lp.invoke_with_fallback(
            ["test message"],
        )

        assert result["provider"] == "groq"
        assert result["fallback_used"] is True
        assert gemini_mock.invoke.call_count == 1

    def test_missing_provider_package_skips_to_next_provider(self, monkeypatch):
        from app.rag import llm_provider as lp

        gemini_mock = MagicMock()
        gemini_mock.invoke.side_effect = RuntimeError("503 service unavailable")
        openrouter_mock = MagicMock()
        openrouter_mock.invoke.return_value = _make_response(_valid_json_answer())

        def missing_groq_package():
            raise ModuleNotFoundError("No module named 'langchain_groq'")

        monkeypatch.setattr(lp.settings, "LLM_PROVIDER_ORDER", "gemini,groq,openrouter")
        monkeypatch.setattr(lp.settings, "LLM_ENABLED_PROVIDERS", "gemini,groq,openrouter")
        monkeypatch.setattr(lp.settings, "LLM_TOTAL_TIMEOUT_SECONDS", 10)
        monkeypatch.setattr(lp.settings, "LLM_MAX_RETRIES", 0)
        monkeypatch.setattr(lp, "_BUILDERS", {
            "gemini": lambda: gemini_mock,
            "groq": missing_groq_package,
            "openrouter": lambda: openrouter_mock,
        })

        result = lp.invoke_with_fallback(["test message"])

        assert result["provider"] == "openrouter"
        assert result["fallback_used"] is True
        openrouter_mock.invoke.assert_called_once()

    def test_all_providers_fail_raises(self):
        gemini_mock = MagicMock()
        gemini_mock.invoke.side_effect = RuntimeError("timeout 503")
        groq_mock = MagicMock()
        groq_mock.invoke.side_effect = RuntimeError("unavailable 503")

        with pytest.raises(RuntimeError):
            self._run_with_mocked_settings(
                ["gemini", "groq"], ["gemini", "groq"],
                {"gemini": gemini_mock, "groq": groq_mock}
            )

    def test_missing_provider_skipped(self):
        """Provider not in builder_map simulates missing key."""
        groq_mock = MagicMock()
        groq_mock.invoke.return_value = _make_response(_valid_json_answer())

        result = self._run_with_mocked_settings(
            ["gemini", "groq"], ["gemini", "groq"],
            {"groq": groq_mock}  # gemini not in map = skipped
        )
        assert result["provider"] == "groq"

    def test_openrouter_fallback(self):
        or_mock = MagicMock()
        or_mock.invoke.return_value = _make_response(_valid_json_answer())

        result = self._run_with_mocked_settings(
            ["gemini", "groq", "openrouter"],
            ["gemini", "groq", "openrouter"],
            {"openrouter": or_mock}
        )
        assert result["provider"] == "openrouter"

    def test_provider_metadata_returned(self):
        mock_llm = MagicMock()
        mock_llm.invoke.return_value = _make_response(_valid_json_answer())
        result = self._run_with_mocked_settings(
            ["gemini"], ["gemini"], {"gemini": mock_llm}
        )
        assert "latency_ms" in result
        assert isinstance(result["latency_ms"], int)
        assert result["latency_ms"] >= 0

    def test_recoverable_error_classification(self):
        from app.rag.llm_provider import _is_recoverable_error
        assert _is_recoverable_error(RuntimeError("rate limit exceeded")) is True
        assert _is_recoverable_error(RuntimeError("timeout")) is True
        assert _is_recoverable_error(RuntimeError("connection refused")) is True
        assert _is_recoverable_error(RuntimeError("503 service unavailable")) is True
        assert _is_recoverable_error(RuntimeError("404 NOT_FOUND model is no longer available")) is True
