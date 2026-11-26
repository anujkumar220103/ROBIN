# Creates and updates the single chatbot configuration for a company.

from sqlalchemy.orm import Session

from app.models.chatbot import Chatbot
from app.models.company import Company


def get_or_create_chatbot(db: Session, company: Company) -> Chatbot:
    chatbot = db.query(Chatbot).filter(Chatbot.company_id == company.id).first()
    if chatbot:
        return chatbot
    chatbot = Chatbot(company_id=company.id, public_id=Chatbot.generate_public_id())
    db.add(chatbot)
    try:
        db.commit()
        db.refresh(chatbot)
        return chatbot
    except Exception:
        db.rollback()
        chatbot = db.query(Chatbot).filter(Chatbot.company_id == company.id).first()
        if chatbot:
            return chatbot
        raise
