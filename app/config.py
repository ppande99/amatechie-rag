from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://app:app@localhost:5432/rag"
    gateway_url: str = "http://localhost:4000"
    gateway_api_key: str = ""
    chat_model: str = "chat-default"
    embed_model: str = "embed-default"
    embed_dim: int = 1024


settings = Settings()
