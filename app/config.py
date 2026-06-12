from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = (
        "postgresql+psycopg2://postgres:postgres@localhost:5432/health_monitor"
    )
    keycloak_url: str = "http://localhost:8080"
    keycloak_realm: str = "health-monitor"
    # When set, the app uses this JSON string as the JWKS directly instead of
    # fetching from Keycloak. Intended for container integration tests only.
    keycloak_jwks_json: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
