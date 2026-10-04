from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Satark Saathi API"
    ENVIRONMENT: str = "development"
    API_PORT: int = 8000
    DATABASE_URL: str = "postgresql+asyncpg://satark_user:satark_password@localhost:5432/satark_db"
    SYNC_DATABASE_URL: str = "postgresql+psycopg://satark_user:satark_password@localhost:5432/satark_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev_secret_key_change_in_production"
    SCREENSHOT_MAX_UPLOAD_BYTES: int = 5 * 1024 * 1024
    VOICE_MAX_UPLOAD_BYTES: int = 10 * 1024 * 1024
    STT_MODEL_SIZE: str = "tiny"
    STT_DEVICE: str = "cpu"
    STT_COMPUTE_TYPE: str = "int8"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
