from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    user: str = Field(validation_alias="POSTGRES_USER", default="postgres")
    password: str = Field(validation_alias="POSTGRES_PASSWORD", default="postgres")
    host: str = Field(validation_alias="POSTGRES_HOST", default="localhost")
    port: str = Field(validation_alias="POSTGRES_PORT", default="5432")
    name: str = Field(validation_alias="POSTGRES_DB", default="postgres")

    model_config = SettingsConfigDict(env_prefix="POSTGRES_")


class AppSettings(BaseSettings):
    openai_api_key: str = Field(validation_alias="OPENAI_API_KEY", default="")
    openai_chat_model: str = Field(default="gpt-4o-mini")
    openai_embedding_model: str = Field(default="text-embedding-3-small")
    vector_store_path: Path = Field(default=Path(".dotdocs/chroma"))
    max_snippet_chars: int = Field(default=1200, description="Hard cap for a single snippet body")
    target_snippet_tokens: int = Field(default=160, description="Ideal size of snippet chunks")
    clerk_api_key: str = Field(validation_alias="CLERK_API_KEY", default="")

    model_config = SettingsConfigDict(env_prefix="APP_", extra="ignore")


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()  # type: ignore[call-arg]

