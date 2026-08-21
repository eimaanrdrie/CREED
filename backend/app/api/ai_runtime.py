from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.ai_runtime import get_ollama_runtime

router = APIRouter(prefix="/ai", tags=["ai-runtime"])


class QwenTestRequest(BaseModel):
    prompt: str = Field(min_length=3, max_length=4000)


@router.get("/runtime")
def runtime_status(refresh: bool = Query(default=False)) -> dict[str, Any]:
    return get_ollama_runtime().runtime_snapshot(refresh=refresh)


@router.post("/test")
def test_qwen(request: QwenTestRequest) -> dict[str, Any]:
    try:
        return get_ollama_runtime().test_prompt(request.prompt)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:  # API boundary: never leak a stack trace to UI.
        raise HTTPException(status_code=502, detail=f"QWEN_TEST_FAILED: {exc.__class__.__name__}") from exc
