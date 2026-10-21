"""Turn text into vectors. The pipeline depends on this small interface, not on Bedrock."""

import hashlib
import math
from typing import Protocol

from app.config import settings
from app.llm import Gateway

BATCH_SIZE = 32


class Embedder(Protocol):
    async def embed(self, texts: list[str]) -> list[list[float]]: ...


class GatewayEmbedder:
    """Real embeddings through the LiteLLM gateway (Bedrock behind it)."""

    def __init__(self, gateway: Gateway | None = None) -> None:
        self._gateway = gateway or Gateway()

    async def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for i in range(0, len(texts), BATCH_SIZE):
            vectors.extend(await self._gateway.embed(texts[i : i + BATCH_SIZE]))
        return vectors


class FakeEmbedder:
    """Deterministic, free, offline. Same text gives the same vector; shared words give
    similar vectors, which is enough to test pipeline logic and wiring (not retrieval quality)."""

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or settings.embed_dim

    async def embed(self, texts: list[str]) -> list[list[float]]:
        return [self._one(t) for t in texts]

    def _one(self, text: str) -> list[float]:
        vec = [0.0] * self.dim
        for word in text.lower().split():
            idx = int.from_bytes(hashlib.md5(word.encode()).digest()[:4], "big") % self.dim
            vec[idx] += 1.0
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        return [v / norm for v in vec]
