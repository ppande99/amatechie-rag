from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/rag"
    gateway_url: str = "http://localhost:4000"
    gateway_api_key: str = ""
    chat_model: str = "chat-default"
    embed_model: str = "embed-default"
    embed_dim: int = 1024

    # Which backends the app uses: "gateway" (LiteLLM) or "bedrock" (direct, your AWS credentials).
    embedder_kind: str = "gateway"
    chat_kind: str = "gateway"
    bedrock_region: str = "us-east-1"
    bedrock_chat_model_id: str = "us.anthropic.claude-haiku-4-5-20251001-v1:0"


settings = Settings()
