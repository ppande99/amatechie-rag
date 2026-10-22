"""Turn text into vectors. The pipeline depends on this small interface, not on Bedrock."""

import asyncio
import hashlib
import json
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


class BedrockEmbedder:
    """Titan Text Embeddings V2 called directly with your AWS credentials (no gateway needed).

    Titan takes one text per request, so calls run in a small thread pool. Needs `pip install boto3`.
    """

    def __init__(
        self, region: str = "us-east-1", model_id: str = "amazon.titan-embed-text-v2:0"
    ) -> None:
        import boto3  # optional dependency, imported lazily

        self._client = boto3.client("bedrock-runtime", region_name=region)
        self._model_id = model_id
        self._dim = settings.embed_dim

    def _one(self, text: str) -> list[float]:
        body = json.dumps({"inputText": text, "dimensions": self._dim, "normalize": True})
        out = self._client.invoke_model(modelId=self._model_id, body=body)
        return json.loads(out["body"].read())["embedding"]

    async def embed(self, texts: list[str]) -> list[list[float]]:
        sem = asyncio.Semaphore(4)

        async def run(t: str) -> list[float]:
            async with sem:
                return await asyncio.to_thread(self._one, t)

        return list(await asyncio.gather(*(run(t) for t in texts)))


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


def make_embedder(kind: str) -> "Embedder":
    if kind == "fake":
        return FakeEmbedder()
    if kind == "bedrock":
        return BedrockEmbedder()
    if kind == "gateway":
        return GatewayEmbedder()
    raise ValueError(f"unknown embedder: {kind}")
