from __future__ import annotations

import httpx

from app.core.config import get_settings
from app.services.embeddings import EmbeddingService


def test_ollama_embed_contract(monkeypatch):
    settings = get_settings()
    object.__setattr__(settings, "embedding_provider", "ollama")
    object.__setattr__(settings, "embedding_allow_hash_fallback", False)
    object.__setattr__(settings, "embedding_model", "qwen3-embedding:0.6b")
    object.__setattr__(settings, "embedding_dimensions", 384)
    captured = {}

    class FakeResponse:
        def raise_for_status(self): pass
        def json(self):
            vector = [0.0] * 384; vector[3] = 1.0
            return {"model": "qwen3-embedding:0.6b", "embeddings": [vector], "total_duration": 10, "prompt_eval_count": 4}

    class FakeClient:
        def __init__(self, *args, **kwargs): pass
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def post(self, url, json):
            captured["url"] = url; captured["json"] = json
            return FakeResponse()

    monkeypatch.setattr(httpx, "Client", FakeClient)
    result = EmbeddingService().embed(["PTP event"])
    assert captured["url"].endswith("/api/embed")
    assert captured["json"]["model"] == "qwen3-embedding:0.6b"
    assert captured["json"]["dimensions"] == 384
    assert result.degraded is False
    assert len(result.vectors[0]) == 384
