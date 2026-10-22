"""Chat models behind one small interface, so the RAG code never knows which backend it uses."""

import asyncio
from typing import Protocol

from app.config import settings
from app.llm import Gateway


class ChatModel(Protocol):
    async def chat(self, system: str, user: str, max_tokens: int = 600) -> str: ...


class GatewayChat:
    """Through the LiteLLM gateway."""

    def __init__(self, gateway: Gateway | None = None) -> None:
        self._gateway = gateway or Gateway()

    async def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
        return await self._gateway.chat(messages, max_tokens=max_tokens, temperature=0)


class BedrockChat:
    """Bedrock Converse API directly with your AWS credentials. Needs boto3."""

    def __init__(self, model_id: str | None = None, region: str | None = None) -> None:
        import boto3  # optional dependency, imported lazily

        self._client = boto3.client(
            "bedrock-runtime", region_name=region or settings.bedrock_region
        )
        self._model_id = model_id or settings.bedrock_chat_model_id

    def _call(self, system: str, user: str, max_tokens: int) -> str:
        out = self._client.converse(
            modelId=self._model_id,
            system=[{"text": system}],
            messages=[{"role": "user", "content": [{"text": user}]}],
            inferenceConfig={"maxTokens": max_tokens, "temperature": 0},
        )
        return out["output"]["message"]["content"][0]["text"]

    async def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        return await asyncio.to_thread(self._call, system, user, max_tokens)


class FakeChat:
    """Canned replies for tests; records what it was asked."""

    def __init__(self, reply: str = "Answer from the passages. [1]") -> None:
        self.reply = reply
        self.calls: list[tuple[str, str]] = []

    async def chat(self, system: str, user: str, max_tokens: int = 600) -> str:
        self.calls.append((system, user))
        return self.reply


def make_chat(kind: str) -> ChatModel:
    if kind == "bedrock":
        return BedrockChat()
    if kind == "gateway":
        return GatewayChat()
    raise ValueError(f"unknown chat backend: {kind}")
