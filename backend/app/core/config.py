from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Content Factory"
    environment: str = "local"
    database_url: str = "sqlite+aiosqlite:///./storage/app.db"
    jwt_secret_key: str = Field(min_length=16, default="change-this-secret-before-production")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 14
    backend_cors_origins: list[AnyHttpUrl | str] = ["http://localhost:3000"]
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_from_email: str = "no-reply@ai-content-factory.local"
    smtp_use_tls: bool = True
    otp_expire_minutes: int = 10
    upload_dir: str = "storage/uploads"
    pollinations_base_url: str = "https://image.pollinations.ai/prompt"
    pollinations_model: str = "flux"
    groq_api_key: str | None = None
    groq_model: str = "openai/gpt-oss-20b"
    groq_api_url: str = "https://api.groq.com/openai/v1/chat/completions"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("backend_cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


def get_settings() -> Settings:
    return Settings()
