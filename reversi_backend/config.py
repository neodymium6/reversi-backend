from typing import ClassVar

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Server settings
    HOST: str
    PORT: int
    RELOAD: bool = False

    # CORS settings
    FRONTEND_ORIGINS: list[str] = []

    # Garbage collection settings
    # Time in seconds after which inactive games are deleted (default: 1 hour)
    GAME_TIMEOUT_SECONDS: int = 3600
    # Interval in seconds between garbage collection runs (default: 10 minutes)
    GC_INTERVAL_SECONDS: int = 600

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(env_file=".env")


settings: Settings = Settings()
