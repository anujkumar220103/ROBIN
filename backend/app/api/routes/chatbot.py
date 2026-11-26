# Manages authenticated chatbot configuration and public embed settings.

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_company, require_company_admin, verify_csrf_token
from app.core.config import settings
from app.db.session import get_db
from app.models.chatbot import Chatbot
from app.models.company import Company
from app.models.document import Document
from app.models.user import User
from app.schemas.chatbot import ChatbotActivate, ChatbotResponse, ChatbotRotate, ChatbotUpdate
from app.services.chatbot_service import get_or_create_chatbot

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.get("", response_model=ChatbotResponse)
def get_chatbot(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    return get_or_create_chatbot(db, current_company)


@router.patch("", response_model=ChatbotResponse)
def update_chatbot(
    data: ChatbotUpdate,
    _csrf: None = Depends(verify_csrf_token),
    _admin: User = Depends(require_company_admin),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    chatbot = get_or_create_chatbot(db, current_company)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(chatbot, field, value)
    db.commit()
    db.refresh(chatbot)
    return chatbot


@router.post("/activate", response_model=ChatbotResponse)
def activate_chatbot(
    data: ChatbotActivate,
    _csrf: None = Depends(verify_csrf_token),
    _admin: User = Depends(require_company_admin),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if not data.acknowledge_public_documents or not data.acknowledge_external_processing:
        raise HTTPException(400, "Both privacy acknowledgements are required.")
    chatbot = get_or_create_chatbot(db, current_company)
    if not chatbot.allowed_domains:
        raise HTTPException(400, "Add at least one allowed website origin.")
    # Sirf ready documents check karte hain — is_publicly_searchable ka activation se
    # koi connection nahi, wo ek alag per-document setting hai.
    ready_count = db.query(func.count(Document.id)).filter(
        Document.company_id == current_company.id,
        Document.status == "ready",
    ).scalar() or 0
    if ready_count == 0:
        raise HTTPException(400, "Process at least one document before activation.")
    chatbot.is_active = True
    db.commit()
    db.refresh(chatbot)
    return chatbot


@router.post("/deactivate", response_model=ChatbotResponse)
def deactivate_chatbot(
    _csrf: None = Depends(verify_csrf_token),
    _admin: User = Depends(require_company_admin),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    chatbot = get_or_create_chatbot(db, current_company)
    chatbot.is_active = False
    db.commit()
    db.refresh(chatbot)
    return chatbot


@router.post("/rotate-id", response_model=ChatbotResponse)
def rotate_chatbot_id(
    data: ChatbotRotate,
    _csrf: None = Depends(verify_csrf_token),
    _admin: User = Depends(require_company_admin),
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    if not data.confirm:
        raise HTTPException(400, "Explicit confirmation is required.")
    chatbot = get_or_create_chatbot(db, current_company)
    chatbot.public_id = Chatbot.generate_public_id()
    chatbot.is_active = False
    db.commit()
    db.refresh(chatbot)
    return chatbot


@router.get("/embed")
def get_embed_code(
    current_company: Company = Depends(get_current_company),
    db: Session = Depends(get_db),
):
    chatbot = get_or_create_chatbot(db, current_company)
    widget_base = settings.PUBLIC_WIDGET_URL.rstrip("/")
    frontend_origin = widget_base[:-len("/widget")] if widget_base.endswith("/widget") else widget_base
    script = f"{frontend_origin}/widget.js"
    return {
        "public_id": chatbot.public_id,
        "is_active": chatbot.is_active,
        "widget_url": settings.PUBLIC_WIDGET_URL,
        "embed_code": f'<script src="{script}" data-robin-chatbot="{chatbot.public_id}" data-robin-widget-base="{widget_base}" async></script>',
    }
