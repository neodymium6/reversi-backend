from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Default to localhost for development, but can be overridden by env var
    FRONTEND_ORIGINS: list[str] = []

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env")


settings: Settings = Settings()
