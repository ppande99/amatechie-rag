"""Thin client for the LiteLLM gateway (OpenAI-compatible). Apps never talk to Bedrock directly."""

import httpx

from app.config import settings


class Gateway:
    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            base_url=settings.gateway_url,
            headers={"Authorization": f"Bearer {settings.gateway_api_key}"},
            timeout=60,
        )

    async def embed(self, texts: list[str]) -> list[list[float]]:
        r = await self._client.post(
            "/v1/embeddings", json={"model": settings.embed_model, "input": texts}
        )
        r.raise_for_status()
        return [d["embedding"] for d in r.json()["data"]]

    async def chat(self, messages: list[dict[str, str]], **kwargs) -> str:
        r = await self._client.post(
            "/v1/chat/completions",
            json={"model": settings.chat_model, "messages": messages, **kwargs},
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
