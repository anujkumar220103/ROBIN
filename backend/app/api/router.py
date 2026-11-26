# Central API router — registers all versioned route modules.

from fastapi import APIRouter

from app.api.routes.auth import router as auth_router
from app.api.routes.company import router as company_router
from app.api.routes.health import router as health_router
from app.api.routes.documents import router as documents_router
from app.api.routes.knowledge_base import router as knowledge_base_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(company_router)
api_router.include_router(documents_router)
api_router.include_router(knowledge_base_router)
