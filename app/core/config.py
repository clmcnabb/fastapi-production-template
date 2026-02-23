from functools import lru_cache

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    environment: str = Field(default="local", alias="ENVIRONMENT")
    database_url: str = Field(
        default="postgresql+psycopg://postgres:postgres@localhost:5432/app", alias="DATABASE_URL"
    )
    jwt_secret_key: str = Field(default="dev-secret", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    model_path: str = Field(default="app/ml/dummy_model.pkl", alias="MODEL_PATH")
    realtime_redis_url: str | None = Field(default=None, alias="REALTIME_REDIS_URL")
    realtime_redis_channel: str = Field(default="realtime:events", alias="REALTIME_REDIS_CHANNEL")

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False
    )

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_secret(cls, value: str, info: ValidationInfo) -> str:
        environment = info.data.get("environment", "local")
        if environment in {"prod", "production"} and value in {
            "",
            "dev-secret",
            "change-me-in-prod",
        }:
            raise ValueError("JWT_SECRET_KEY must be set to a secure value in production")
        return value

    @field_validator("realtime_redis_url")
    @classmethod
    def empty_redis_url_to_none(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
