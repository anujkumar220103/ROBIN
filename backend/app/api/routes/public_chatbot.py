# Handles public chatbot discovery, sessions, and website visitor chat requests.

import re
import time
import uuid
from collections import defaultdict
from threading import Lock

import jwt
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.widget_security import create_widget_session, verify_widget_session
from app.db.session import get_db
from app.models.chatbot import Chatbot
from app.models.company import Company
from app.rag.pipeline import run_rag_pipeline
from app.schemas.chat import ConversationMessage
from app.schemas.chatbot import PublicChatbotResponse
from app.schemas.public_chat import PublicChatRequest, PublicChatResponse, PublicSessionResponse, PublicSource
from app.services.domain_service import normalize_origin, origin_is_allowed

router = APIRouter(prefix="/public/chatbots", tags=["Public Chatbot"])

_limit_lock = Lock()
_session_times: dict[str, list[float]] = defaultdict(list)
_chat_times: dict[str, list[float]] = defaultdict(list)
_concurrent_companies: dict[str, int] = defaultdict(int)
_concurrent_global = 0
_daily_company: dict[str, int] = defaultdict(int)
_daily_global = 0


def _bounded_limit(key: str, store: dict, limit: int) -> bool:
    now = time.monotonic()
    with _limit_lock:
        store[key] = [timestamp for timestamp in store[key] if now - timestamp < 60]
        if len(store[key]) >= limit:
            return False
        store[key].append(now)
        return True


def _client_origin(request: Request, embedding_origin: str | None) -> str:
    origin = embedding_origin or request.headers.get("origin")
    if not origin:
        referer = request.headers.get("referer")
        if referer:
            try:
                origin = normalize_origin(referer)
            except ValueError:
                origin = None
    if not origin:
        raise HTTPException(403, "Website origin is required.")
    try:
        return normalize_origin(origin)
    except ValueError as exc:
        raise HTTPException(403, str(exc)) from exc


def _resolve_chatbot(db: Session, public_id: str) -> tuple[Chatbot, Company]:
    chatbot = db.query(Chatbot).filter(Chatbot.public_id == public_id).first()
    if chatbot is None or not chatbot.is_active:
        raise HTTPException(404, "Chatbot is unavailable.")
    company = db.query(Company).filter(Company.id == chatbot.company_id).first()
    if company is None or not company.is_active:
        raise HTTPException(404, "Chatbot is unavailable.")
    return chatbot, company


def _public_config(chatbot: Chatbot) -> PublicChatbotResponse:
    return PublicChatbotResponse(
        public_id=chatbot.public_id,
        name=chatbot.name,
        description=chatbot.description,
        welcome_message=chatbot.welcome_message,
        placeholder=chatbot.placeholder,
        primary_color=chatbot.primary_color,
        position=chatbot.position,
        launcher_label=chatbot.launcher_label,
        suggested_questions=chatbot.suggested_questions,
        show_sources=chatbot.show_sources,
    )


@router.get("/{public_id}/config", response_model=PublicChatbotResponse)
def public_config(
    public_id: str,
    request: Request,
    x_robin_origin: str | None = Header(default=None, alias="X-Robin-Origin"),
    db: Session = Depends(get_db),
):
    chatbot, _ = _resolve_chatbot(db, public_id)
    origin = _client_origin(request, x_robin_origin)
    if not origin_is_allowed(chatbot.allowed_domains, origin):
        raise HTTPException(403, "This website is not allowed to use this chatbot.")
    return _public_config(chatbot)


@router.post("/{public_id}/session", response_model=PublicSessionResponse)
def create_public_session(
    public_id: str,
    request: Request,
    x_robin_origin: str | None = Header(default=None, alias="X-Robin-Origin"),
    db: Session = Depends(get_db),
):
    if not _bounded_limit(request.client.host if request.client else "unknown", _session_times, settings.PUBLIC_SESSION_RATE_LIMIT_PER_MINUTE):
        raise HTTPException(status_code=429, detail="Too many session requests.", headers={"Retry-After": "60"})
    chatbot, _ = _resolve_chatbot(db, public_id)
    origin = _client_origin(request, x_robin_origin)
    if not origin_is_allowed(chatbot.allowed_domains, origin):
        raise HTTPException(403, "This website is not allowed to use this chatbot.")
    try:
        token, expires_in = create_widget_session(public_id, origin)
    except RuntimeError as exc:
        raise HTTPException(503, "Public chat is temporarily unavailable.") from exc
    return PublicSessionResponse(session_token=token, expires_in=expires_in, chatbot=_public_config(chatbot))


@router.post("/{public_id}/ask", response_model=PublicChatResponse)
def public_ask(
    public_id: str,
    data: PublicChatRequest,
    request: Request,
    authorization: str | None = Header(default=None),
    x_robin_origin: str | None = Header(default=None, alias="X-Robin-Origin"),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Widget session required.")
    chatbot, company = _resolve_chatbot(db, public_id)
    origin = _client_origin(request, x_robin_origin)
    if not origin_is_allowed(chatbot.allowed_domains, origin):
        raise HTTPException(403, "This website is not allowed to use this chatbot.")
    try:
        verify_widget_session(authorization[7:].strip(), public_id, origin)
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired widget session.")

    ip_key = request.client.host if request.client else "unknown"
    if not _bounded_limit(ip_key, _chat_times, settings.PUBLIC_CHAT_IP_RATE_LIMIT_PER_MINUTE):
        raise HTTPException(status_code=429, detail="Too many public chat requests.", headers={"Retry-After": "60"})

    global _concurrent_global, _daily_global
    company_key = str(company.id)
    with _limit_lock:
        if _concurrent_companies[company_key] >= settings.PUBLIC_CHAT_MAX_CONCURRENT_PER_COMPANY:
            raise HTTPException(429, "Too many concurrent requests for this chatbot.")
        if _concurrent_global >= settings.PUBLIC_CHAT_MAX_CONCURRENT_GLOBAL:
            raise HTTPException(429, "Public chat capacity is temporarily full.")
        if _daily_company[company_key] >= settings.PUBLIC_CHAT_COMPANY_DAILY_LIMIT:
            raise HTTPException(429, "Daily chatbot limit reached.")
        if _daily_global >= settings.PUBLIC_CHAT_GLOBAL_DAILY_LIMIT:
            raise HTTPException(429, "Global public chat limit reached.")
        _concurrent_companies[company_key] += 1
        _concurrent_global += 1
        _daily_company[company_key] += 1
        _daily_global += 1

    try:
        history = [ConversationMessage(role=item.role, content=item.content) for item in data.history]
        result = run_rag_pipeline(
            db=db,
            company_id=company.id,
            question=data.question,
            history=history,
            request_id=str(uuid.uuid4()),
            public_only=True,
        )
    except Exception:
        raise HTTPException(503, "Knowledge assistant is temporarily unavailable.")
    finally:
        with _limit_lock:
            _concurrent_companies[company_key] -= 1
            _concurrent_global -= 1

    if result["status"] in ("invalid_input", "retrieval_error", "provider_error", "validation_error"):
        raise HTTPException(503 if result["status"] != "invalid_input" else 422, result["answer"])

    if not chatbot.show_sources:
        answer = re.sub(r"\s*\[\d+\]", "", result["answer"])
        return PublicChatResponse(request_id=result["request_id"], status=result["status"], answer=answer, sources=[])

    sources = []
    seen = set()
    for source in result.get("sources", []):
        document_id = str(source["document_id"])
        if document_id in seen:
            continue
        seen.add(document_id)
        title = source["filename"]
        title = title.rsplit(".", 1)[0] if title else "Published document"
        sources.append(PublicSource(source_number=len(sources) + 1, title=title, page_number=source["page_number"]))
    return PublicChatResponse(request_id=result["request_id"], status=result["status"], answer=result["answer"], sources=sources)
