from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Đọc .env ở thư mục gốc repo khi chạy từ backend/, hoặc .env cạnh nơi chạy lệnh.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    test_database_url: str | None = None

    storage_dir: Path = Field(
        default=Path("storage"), validation_alias=AliasChoices("FILE_STORAGE_DIR", "STORAGE_DIR")
    )
    max_upload_mb: int = Field(default=20, gt=0)
    app_timezone: str = "Asia/Ho_Chi_Minh"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_e5_small_v1"

    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    stt_model: str = "small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
