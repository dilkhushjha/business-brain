from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    database_url: str = "postgresql://business_brain:business_brain@localhost:5432/business_brain"
    redis_url: str = "redis://localhost:6379/0"
    connector_registration_key: str | None = None
    jwt_secret_key: str = "development-only-change-this-jwt-secret"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30
    password_reset_expire_minutes: int = 30
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    allowed_hosts: str = "localhost,127.0.0.1"
    max_upload_bytes: int = 25_000_000
    enable_api_docs: bool = True
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_tls: bool = True
    password_reset_url: str = "http://localhost:3000/reset-password"

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
        if not self.jwt_secret_key or self.jwt_secret_key == "development-only-change-this-jwt-secret" or len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be a strong secret of at least 32 characters in production")
        if self.access_token_expire_minutes < 5 or self.access_token_expire_minutes > 1440:
            raise ValueError("ACCESS_TOKEN_EXPIRE_MINUTES must be between 5 and 1440")
        if self.refresh_token_expire_days < 1 or self.refresh_token_expire_days > 90:
            raise ValueError("REFRESH_TOKEN_EXPIRE_DAYS must be between 1 and 90")
        if self.password_reset_expire_minutes < 10 or self.password_reset_expire_minutes > 120:
            raise ValueError("PASSWORD_RESET_EXPIRE_MINUTES must be between 10 and 120")
        if "localhost" in self.database_url or "127.0.0.1" in self.database_url:
            raise ValueError("DATABASE_URL must point to a remote production database")
        if not self.cors_origin_list or any(origin.startswith("http://localhost") for origin in self.cors_origin_list):
            raise ValueError("CORS_ORIGINS must contain the deployed frontend origin in production")
        if not self.allowed_host_list or "*" in self.allowed_host_list:
            raise ValueError("ALLOWED_HOSTS must explicitly list production hosts")
        if self.max_upload_bytes <= 0:
            raise ValueError("MAX_UPLOAD_BYTES must be positive")
        if not self.smtp_host or not self.smtp_from:
            raise ValueError("SMTP_HOST and SMTP_FROM must be configured in production")
        if not self.password_reset_url.startswith("https://"):
            raise ValueError("PASSWORD_RESET_URL must use HTTPS in production")
        return self


settings = Settings()
