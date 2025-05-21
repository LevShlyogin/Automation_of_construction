from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # --- FastAPI ---
    PROJECT_NAME: str = "Rod Calculator"
    API_V1_STR: str   = "/rod-calc/api/v1"

    # --- DB ---
    SQLALCHEMY_DATABASE_URI: str

    # --- Celery / RabbitMQ ---
    CELERY_BROKER_URL:  str
    CELERY_BACKEND_URL: str | None = None

    # --- Sentry ---
    SENTRY_DSN: str | None = None
    ENVIRONMENT: str = "local"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings:
    return Settings()
