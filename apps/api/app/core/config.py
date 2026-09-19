from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql://business_brain:business_brain@localhost:5432/business_brain"
    redis_url: str = "redis://localhost:6379/0"
    connector_registration_key: str | None = None
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_hosts: str = "localhost,127.0.0.1"
    max_upload_bytes: int = 25_000_000
    enable_api_docs: bool = True

    @property
    def is_production(self) -> bool:
        return self.app_env.lower() in {"production", "prod"}

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def allowed_host_list(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]

    @model_validator(mode="after")
    def validate_production_configuration(self):
        if not self.is_production:
            return self
        if not self.connector_registration_key:
            raise ValueError("CONNECTOR_REGISTRATION_KEY must be configured in production")
        if self.connector_registration_key.strip().lower() in {"change-me", "changeme", "secret"}:
            raise ValueError("CONNECTOR_REGISTRATION_KEY must not use a placeholder value")
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            raise ValueError("DATABASE_URL must point to a remote production database")
        if not self.cors_origin_list or any(origin.startswith("http://localhost") for origin in self.cors_origin_list):
            raise ValueError("CORS_ORIGINS must contain the deployed frontend origin in production")
        if not self.allowed_host_list or "*" in self.allowed_host_list:
            raise ValueError("ALLOWED_HOSTS must explicitly list production hosts")
        if self.max_upload_bytes <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be positive")
        return self


settings = Settings()
