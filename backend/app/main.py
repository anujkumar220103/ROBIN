# FastAPI application entry point — initializes the app, middleware, and routes.

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings

# Basic logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI):
    # Interrupted ingestion is not left in a permanently processing state.
    try:
        from app.db.session import SessionLocal
        from app.models.document import Document
        db = SessionLocal()
        try:
            interrupted = db.query(Document).filter(
                Document.status == "processing"
            ).update(
                {
                    Document.status: "failed",
                    Document.error_message: "Document processing was interrupted. You can retry it.",
                },
                synchronize_session=False,
            )
            db.commit()
            if interrupted:
                logger.warning("Marked %d interrupted documents as failed.", interrupted)
        finally:
            db.close()
    except Exception:
        logger.exception("Document startup recovery could not access the database.")
    yield

app = FastAPI(
    title=settings.APP_NAME,
    description="Retrieval-Oriented Bot for Intelligent Navigation",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if settings.is_production:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Public chatbot API endpoints are called by the ROBIN frontend running inside
    # an iframe hosted on the ROBIN origin — not framed directly by external sites.
    # Keeping X-Frame-Options: DENY on JSON responses is harmless but add it only
    # for non-public paths so the header remains accurate.
    path = request.url.path
    if not path.startswith(f"{settings.API_V1_PREFIX}/public/"):
        response.headers["X-Frame-Options"] = "DENY"

    return response

# ---------------------------------------------------------------------------
# CORS Middleware
# ---------------------------------------------------------------------------
# CORS wildcard origins allow_credentials ke saath use nahi kar sakte.
# Explicit origins list karte hain — environment variables se load hoti hai.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-CSRF-Token"],
)

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.get("/", include_in_schema=False)
def root():
    """Root endpoint — simple liveness indicator."""
    return JSONResponse(content={
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": f"{settings.APP_NAME} API is running",
    })
