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
    # Comma-separated list of origins permitted by the CORS middleware.
    cors_allowed_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_allowed_origins_list(self) -> list[str]:
        return [
            origin.strip()
            for origin in self.cors_allowed_origins.split(",")
            if origin.strip()
        ]


settings = Settings()
