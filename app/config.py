from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg2://postgres:vasanth@localhost:5432/taskdb"
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env")

    @field_validator("database_url")
    @classmethod
    def clean_database_url(cls, v: str) -> str:
        v = v.strip().strip("'\"")
        if v.startswith("psql "):
            v = v[5:].strip().strip("'\"")
        for prefix in ("postgres://", "postgresql://"):
            if v.startswith(prefix):
                v = "postgresql+psycopg2://" + v[len(prefix):]
                break
        return v


settings = Settings()