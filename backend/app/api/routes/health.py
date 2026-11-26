# Health check endpoints — used to verify that the API and database are running.

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.db.session import check_database_connection
from app.schemas.health import DatabaseHealthResponse, HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", response_model=HealthResponse)
def health_check():
    """Basic liveness check — does not depend on database availability."""
    return HealthResponse(
        status="healthy",
        service=settings.APP_NAME,
        version=settings.APP_VERSION,
    )


@router.get("/db", response_model=DatabaseHealthResponse)
def database_health_check():
    """Check database connectivity with a lightweight SELECT 1 query."""
    connected = check_database_connection()

    if connected:
        return DatabaseHealthResponse(status="healthy", database="connected")

    # Sensitive information expose nahi karte — sirf status return karte hain.
    return JSONResponse(
        status_code=503,
        content={"status": "unhealthy", "database": "disconnected"},
    )


@router.get("/ready")
def readiness_check():
    """Report whether required runtime dependencies are available."""
    database_ready = check_database_connection()
    vector_ready = True
    try:
        from app.rag.vector_store import get_vector_store
        get_vector_store().check_connection()
    except Exception:
        vector_ready = False

    ready = database_ready and vector_ready
    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "unavailable",
            "database": "ready" if database_ready else "unavailable",
            "vector_store": "ready" if vector_ready else "unavailable",
        },
    )
