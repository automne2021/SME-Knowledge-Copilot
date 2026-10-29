from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Đọc .env ở thư mục gốc repo khi chạy từ backend/, hoặc .env cạnh nơi chạy lệnh.
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str
    test_database_url: str | None = None

    storage_dir: Path = Path("storage")
    max_upload_mb: int = 25
    app_timezone: str = "Asia/Ho_Chi_Minh"

    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    stt_model: str = "small"


@lru_cache
def get_settings() -> Settings:
    return Settings()
