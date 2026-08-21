from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from typing import Iterable

import httpx

from app.core.config import get_settings

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-/]{1,}")


class EmbeddingError(RuntimeError):
    pass


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: list[list[float]]
    provider: str
    model: str
    dimensions: int
    degraded: bool
    total_duration_ns: int | None = None
    prompt_eval_count: int | None = None


def _l2_normalize(values: list[float]) -> list[float]:
    norm = math.sqrt(sum(v * v for v in values))
    if norm == 0:
        return values
    return [v / norm for v in values]


def hashing_embedding(text: str, dimensions: int) -> list[float]:
    """Deterministic offline vector fallback. It is local but lexical, not a neural embedding model."""
    vector = [0.0] * dimensions
    tokens = [m.group(0).lower() for m in TOKEN_RE.finditer(text)]
    for token in tokens:
        for feature in (token, f"w:{token}"):
            digest = hashlib.blake2b(feature.encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % dimensions
            vector[index] += 1.0
        # Adjacent character trigrams improve robustness to identifiers and spelling variants.
        padded = f"^{token}$"
        for i in range(max(0, len(padded) - 2)):
            trigram = padded[i : i + 3]
            digest = hashlib.blake2b(f"c:{trigram}".encode("utf-8"), digest_size=16).digest()
            index = int.from_bytes(digest[:8], "big") % dimensions
            vector[index] += 0.35
    return _l2_normalize(vector)


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()

    def embed(self, texts: Iterable[str]) -> EmbeddingBatch:
        items = [text.strip() for text in texts]
        if not items or any(not item for item in items):
            raise EmbeddingError("EMPTY_EMBEDDING_INPUT")

        provider = self.settings.embedding_provider.lower()
        if provider == "ollama":
            try:
                return self._embed_ollama(items)
            except Exception as exc:
                if not self.settings.embedding_allow_hash_fallback:
                    raise EmbeddingError(f"OLLAMA_EMBEDDING_FAILED: {exc.__class__.__name__}: {exc}") from exc
                vectors = [hashing_embedding(text, self.settings.embedding_dimensions) for text in items]
                return EmbeddingBatch(
                    vectors=vectors,
                    provider="hashing-fallback",
                    model="creed-hash-v1",
                    dimensions=self.settings.embedding_dimensions,
                    degraded=True,
                )
        if provider == "hashing":
            vectors = [hashing_embedding(text, self.settings.embedding_dimensions) for text in items]
            return EmbeddingBatch(
                vectors=vectors,
                provider="hashing",
                model="creed-hash-v1",
                dimensions=self.settings.embedding_dimensions,
                degraded=True,
            )
        raise EmbeddingError(f"UNSUPPORTED_EMBEDDING_PROVIDER: {provider}")

    def _embed_ollama(self, items: list[str]) -> EmbeddingBatch:
        payload = {
            "model": self.settings.embedding_model,
            "input": items,
            "dimensions": self.settings.embedding_dimensions,
            "truncate": True,
        }
        with httpx.Client(timeout=self.settings.embedding_timeout_seconds) as client:
            response = client.post(f"{self.settings.ollama_base_url.rstrip('/')}/api/embed", json=payload)
            response.raise_for_status()
            body = response.json()
        vectors = body.get("embeddings")
        if not isinstance(vectors, list) or len(vectors) != len(items):
            raise EmbeddingError("INVALID_OLLAMA_EMBEDDING_RESPONSE")
        parsed: list[list[float]] = []
        for vector in vectors:
            if not isinstance(vector, list) or len(vector) != self.settings.embedding_dimensions:
                raise EmbeddingError("EMBEDDING_DIMENSION_MISMATCH")
            parsed.append(_l2_normalize([float(v) for v in vector]))
        return EmbeddingBatch(
            vectors=parsed,
            provider="ollama",
            model=str(body.get("model") or self.settings.embedding_model),
            dimensions=self.settings.embedding_dimensions,
            degraded=False,
            total_duration_ns=body.get("total_duration"),
            prompt_eval_count=body.get("prompt_eval_count"),
        )

    def health(self) -> dict[str, object]:
        try:
            probe = self.embed(["CREED embedding health check"])
            return {
                "status": "DEGRADED" if probe.degraded else "READY",
                "provider": probe.provider,
                "model": probe.model,
                "dimensions": probe.dimensions,
                "degraded": probe.degraded,
                "error": None,
            }
        except EmbeddingError as exc:
            return {
                "status": "UNAVAILABLE",
                "provider": self.settings.embedding_provider,
                "model": self.settings.embedding_model,
                "dimensions": self.settings.embedding_dimensions,
                "degraded": False,
                "error": str(exc),
            }
