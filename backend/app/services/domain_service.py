# Normalizes and validates exact website origins allowed to embed a chatbot.

from urllib.parse import urlsplit

from app.core.config import settings


def normalize_origin(value: str) -> str:
    value = value.strip()
    if not value or "*" in value:
        raise ValueError("Wildcard origins are not allowed.")

    parsed = urlsplit(value)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only HTTP and HTTPS origins are allowed.")
    if parsed.username or parsed.password:
        raise ValueError("Credentials are not allowed in origins.")
    if parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        raise ValueError("Origins must not include paths, queries, or fragments.")
    if not parsed.hostname:
        raise ValueError("Origin hostname is required.")

    host = parsed.hostname.lower().rstrip(".")
    is_local = host in ("localhost", "127.0.0.1", "::1")
    if parsed.scheme == "http" and not (settings.APP_ENV == "development" and is_local):
        raise ValueError("Production origins must use HTTPS.")

    port = parsed.port
    if (parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80):
        port = None
    return f"{parsed.scheme}://{host}" + (f":{port}" if port else "")


def origin_is_allowed(allowed_domains: list[str], origin: str) -> bool:
    try:
        normalized = normalize_origin(origin)
    except (ValueError, UnicodeError):
        return False
    return normalized in {normalize_origin(item) for item in allowed_domains if item}
