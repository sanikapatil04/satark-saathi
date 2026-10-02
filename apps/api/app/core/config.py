from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Satark Saathi API"
    ENVIRONMENT: str = "development"
    API_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://satark_user:satark_password@localhost:5432/satark_db"
    SYNC_DATABASE_URL: str = "postgresql+psycopg://satark_user:satark_password@localhost:5432/satark_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev_secret_key_change_in_production"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
