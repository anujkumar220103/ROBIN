# Configures supported LLM providers and automatic fallback behavior.
# Primary provider fail hone par next available LLM use karte hain.

import logging
import time
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)

# Recoverable HTTP status codes — in par fallback try karte hain.
RECOVERABLE_STATUS_CODES = {404, 429, 500, 502, 503, 504}


def _is_model_unavailable_error(exc: Exception) -> bool:
    """Detect retired or invalid provider models so fallback happens immediately."""
    message = str(exc).lower()
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    return (
        status_code == 404
        or "not_found" in message
        or "model not found" in message
        or "model is no longer available" in message
    )


def _is_recoverable_error(exc: Exception) -> bool:
    """Determine whether an exception warrants trying the next provider."""
    msg = str(exc).lower()

    # Rate limiting, quota, temporary unavailability — ye sab recoverable hain.
    recoverable_keywords = [
        "rate limit", "quota", "too many requests", "unavailable",
        "timeout", "timed out", "connection", "overloaded", "capacity",
        "503", "502", "504", "500", "internal server error",
        "404", "not_found", "model not found", "model not available",
        "model is currently", "model is no longer available", "try again",
    ]
    for keyword in recoverable_keywords:
        if keyword in msg:
            return True

    # HTTP status code check karo agar exception mein code hai.
    status_code = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if status_code in RECOVERABLE_STATUS_CODES:
        return True

    return False


def _build_gemini():
    """Create a ChatGoogleGenerativeAI client using configured settings."""
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not configured.")
    from langchain_google_genai import ChatGoogleGenerativeAI
    return ChatGoogleGenerativeAI(
        model=settings.GEMINI_MODEL,
        google_api_key=settings.GEMINI_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_output_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        max_retries=0,  # Retry is handled by our own fallback loop.
        timeout=settings.LLM_PROVIDER_TIMEOUT_SECONDS,
    )


def _build_groq():
    """Create a ChatGroq client using configured settings."""
    if not settings.GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY is not configured.")
    from langchain_groq import ChatGroq
    return ChatGroq(
        model=settings.GROQ_MODEL,
        api_key=settings.GROQ_API_KEY,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        max_retries=0,
        timeout=settings.LLM_PROVIDER_TIMEOUT_SECONDS,
    )


def _build_openrouter():
    """Create a ChatOpenAI client pointed at OpenRouter's compatible endpoint."""
    if not settings.OPENROUTER_API_KEY:
        raise ValueError("OPENROUTER_API_KEY is not configured.")
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=settings.OPENROUTER_MODEL,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_OUTPUT_TOKENS,
        max_retries=0,
        timeout=settings.LLM_PROVIDER_TIMEOUT_SECONDS,
    )


_BUILDERS = {
    "gemini": _build_gemini,
    "groq": _build_groq,
    "openrouter": _build_openrouter,
}

_MODEL_NAMES = {
    "gemini": lambda: settings.GEMINI_MODEL,
    "groq": lambda: settings.GROQ_MODEL,
    "openrouter": lambda: settings.OPENROUTER_MODEL,
}


def get_configured_providers() -> list[dict]:
    """Return safe configuration status for each known provider.

    API keys ko expose nahi karte — sirf 'configured' boolean return hota hai.
    """
    result = []
    for name in ["gemini", "groq", "openrouter"]:
        api_key = getattr(settings, f"{name.upper()}_API_KEY", "")
        is_configured = bool(api_key)
        is_enabled = name in settings.enabled_providers
        result.append({
            "name": name,
            "configured": is_configured,
            "enabled": is_enabled and is_configured,
        })
    return result


def invoke_with_fallback(messages: list) -> dict:
    """Invoke configured LLM providers in order, with automatic fallback.

    Ek provider fail hone par next configured provider try karta hai.
    Sirf recoverable failures par fallback hota hai — invalid input, security
    failures, aur insufficient context par fallback nahi hota.

    Returns a dict with: answer_text, provider, model, fallback_used, latency_ms
    """
    # Configured priority order se enabled providers filter karo.
    ordered = [
        p for p in settings.provider_order
        if p in settings.enabled_providers
    ]

    if not ordered:
        raise RuntimeError(
            "No LLM providers are configured. Add at least one provider API key."
        )

    overall_start = time.monotonic()
    last_error: Optional[Exception] = None
    fallback_used = False

    for index, provider_name in enumerate(ordered):
        # Overall deadline check — agar time nahi bacha to provider try mat karo.
        elapsed_ms = int((time.monotonic() - overall_start) * 1000)
        remaining_seconds = settings.LLM_TOTAL_TIMEOUT_SECONDS - elapsed_ms / 1000
        if remaining_seconds < 2:
            logger.warning("Overall generation deadline exceeded before trying %s.", provider_name)
            break

        if index > 0:
            fallback_used = True
            logger.info("Falling back to provider: %s", provider_name)

        # Provider client banao — agar configuration missing hai to skip karo.
        try:
            llm = _BUILDERS[provider_name]()
        except (ValueError, KeyError, ImportError) as exc:
            logger.warning("Provider %s skipped: %s", provider_name, exc)
            last_error = exc
            continue

        model_name = _MODEL_NAMES[provider_name]()

        # Bounded retry loop — ek extra attempt allow karte hain recoverable errors par.
        for attempt in range(settings.LLM_MAX_RETRIES + 1):
            provider_start = time.monotonic()
            try:
                response = llm.invoke(messages)
                latency_ms = int((time.monotonic() - provider_start) * 1000)
                content = response.content if hasattr(response, "content") else str(response)
                logger.info(
                    "Provider %s (%s) succeeded in %dms (attempt %d, fallback=%s).",
                    provider_name, model_name, latency_ms, attempt + 1, fallback_used,
                )
                return {
                    "answer_text": content,
                    "provider": provider_name,
                    "model": model_name,
                    "fallback_used": fallback_used,
                    "latency_ms": int((time.monotonic() - overall_start) * 1000),
                }
            except Exception as exc:
                last_error = exc
                latency_ms = int((time.monotonic() - provider_start) * 1000)
                if _is_model_unavailable_error(exc):
                    logger.warning(
                        "Provider %s model is unavailable; trying the next provider.",
                        provider_name,
                    )
                    break
                if _is_recoverable_error(exc):
                    if attempt < settings.LLM_MAX_RETRIES:
                        logger.warning(
                            "Provider %s attempt %d failed (recoverable): %s. Retrying.",
                            provider_name, attempt + 1, type(exc).__name__,
                        )
                        time.sleep(min(1.0, 0.5 * (attempt + 1)))
                        continue
                    else:
                        logger.warning(
                            "Provider %s exhausted retries after %dms: %s",
                            provider_name, latency_ms, type(exc).__name__,
                        )
                        break  # Try next provider.
                else:
                    # Non-recoverable — safety refusal ya config error.
                    logger.warning(
                        "Provider %s non-recoverable error: %s",
                        provider_name, type(exc).__name__,
                    )
                    # Agar credentials invalid hain to same provider retry mat karo.
                    if any(k in str(exc).lower() for k in ["api key", "unauthorized", "authentication", "invalid_api_key"]):
                        break
                    # Other non-recoverable errors — do not try next provider automatically.
                    raise

    total_ms = int((time.monotonic() - overall_start) * 1000)
    raise RuntimeError(
        f"All configured LLM providers failed after {total_ms}ms. "
        f"Last error: {type(last_error).__name__}: {last_error}"
    )
