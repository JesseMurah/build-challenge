from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    telegram_bot_token: str
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_gemini_provider():
    from google import genai
    from app.infrastructure.gemini_provider import GeminiProvider

    settings = get_settings()
    client = genai.Client(api_key=settings.gemini_api_key)
    return GeminiProvider(client=client)
