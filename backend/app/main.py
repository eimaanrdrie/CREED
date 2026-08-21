import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.ai_runtime import router as ai_runtime_router
from app.api.health import router as health_router
from app.api.domain import router as domain_router
from app.api.documents import router as documents_router
from app.api.retrieval import router as retrieval_router
from app.api.issues import router as issues_router
from app.api.issue_understanding import router as issue_understanding_router
from app.api.analysis_runs import router as analysis_runs_router
from app.api.advanced import router as advanced_router
from app.core.ai_runtime import get_ollama_runtime
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.ollama_warm_on_startup:
        try:
            await asyncio.to_thread(get_ollama_runtime().warm_model)
        except Exception as exc:
            # The API remains available in a truthful degraded state if Ollama is offline.
            logger.warning("Ollama warm-up failed: %s: %s", exc.__class__.__name__, exc)
    yield

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="CREED project delivery intelligence API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-CREED-Original-Verified", "X-CREED-Content-SHA256", "Content-Disposition"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(ai_runtime_router, prefix="/api/v1")
app.include_router(domain_router, prefix="/api/v1")
app.include_router(documents_router, prefix="/api/v1")
app.include_router(retrieval_router, prefix="/api/v1")
app.include_router(issues_router, prefix="/api/v1")
app.include_router(issue_understanding_router, prefix="/api/v1")
app.include_router(analysis_runs_router, prefix="/api/v1")
app.include_router(advanced_router, prefix="/api/v1")

@app.get("/")
def root() -> dict[str, str]:
    return {"service": settings.app_name, "status": "running", "docs": "/docs"}
