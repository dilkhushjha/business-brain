from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    database_url: str = "postgresql://business_brain:business_brain@localhost:5432/business_brain"
    redis_url: str = "redis://localhost:6379/0"
    connector_registration_key: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
