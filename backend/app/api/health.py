from datetime import datetime, timezone
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.ai_runtime import get_ollama_runtime
from app.core.config import get_settings
from app.core.database import database_health
from app.services.documents import knowledge_storage_health

router = APIRouter(tags=["health"])

class Dependencies(BaseModel):
    api: str
    database: str
    qwen: str
    knowledge_source: str

class HealthResponse(BaseModel):
    service: str
    status: str
    version: str
    environment: str
    timestamp: datetime
    dependencies: Dependencies

@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    settings = get_settings()
    database_state, _ = database_health()
    qwen_probe = get_ollama_runtime().runtime_snapshot(refresh=False)
    qwen_state = "CONNECTED" if qwen_probe["status"] == "READY" else "UNAVAILABLE"
    knowledge_state, _ = knowledge_storage_health(settings.document_storage_dir)
    degraded = database_state == "UNAVAILABLE" or qwen_state == "UNAVAILABLE" or knowledge_state == "UNAVAILABLE"
    return HealthResponse(
        service=settings.app_name,
        status="degraded" if degraded else "ok",
        version=settings.app_version,
        environment=settings.app_env,
        timestamp=datetime.now(timezone.utc),
        dependencies=Dependencies(
            api="CONNECTED",
            database=database_state,
            qwen=qwen_state,
            knowledge_source=knowledge_state,
        ),
    )

@router.get("/health/live")
def liveness() -> dict[str, str]:
    return {"status": "ok"}
