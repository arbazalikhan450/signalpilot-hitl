from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    project_name: str = "SignalPilot"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    frontend_port: int = 5173
    log_level: str = "INFO"

    postgres_db: str = "social_ai"
    postgres_user: str = "social_ai"
    postgres_password: str = "changeme"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    redis_url: str = "redis://localhost:6379/0"

    openai_api_key: str = Field(default="change-me", alias="OPENAI_API_KEY")
    openai_model: str = "gpt-4.1-mini"
    app_secret_key: str = "change-this-secret"
    token_encryption_key: str = "change-this-32-char-key"

    x_client_id: str = ""
    x_client_secret: str = ""
    x_redirect_uri: str = "http://localhost:8000/api/v1/oauth/x/callback"
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = "http://localhost:8000/api/v1/oauth/linkedin/callback"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
