from functools import lru_cache
from pathlib import Path

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Đọc .env ở thư mục gốc repo khi chạy từ backend/, hoặc .env cạnh nơi chạy lệnh.
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"), extra="ignore", hide_input_in_errors=True
    )

    database_url: str
    test_database_url: str | None = None

    storage_dir: Path = Field(
        default=Path("storage"), validation_alias=AliasChoices("FILE_STORAGE_DIR", "STORAGE_DIR")
    )
    max_upload_mb: int = Field(default=20, gt=0)
    max_pdf_pages: int = Field(default=200, gt=0)
    max_docx_uncompressed_mb: int = Field(default=100, gt=0)
    max_docx_zip_entries: int = Field(default=2000, gt=0)
    parser_timeout_seconds: float = Field(default=60, gt=0)
    max_extracted_chars: int = Field(default=2_000_000, gt=0)
    max_source_blocks: int = Field(default=20_000, gt=0)
    max_document_chunks: int = Field(default=5000, gt=0)
    chunk_size_tokens: int = Field(default=350, gt=0, le=512)
    chunk_overlap_tokens: int = Field(default=50, ge=0)
    embedding_model: str = "intfloat/multilingual-e5-small"
    embedding_revision: str = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
    hf_home: Path = Path("D:/AI-Cache/sme-copilot/huggingface")
    embedding_dimension: int = Field(default=384, ge=384, le=384)
    embedding_device: str = "cpu"
    embedding_batch_size: int = Field(default=4, ge=1, le=16)
    embedding_threads: int = Field(default=2, ge=1, le=8)
    embedding_timeout_seconds: float = Field(default=120, gt=0)
    vector_timeout_seconds: float = Field(default=10, gt=0)
    job_max_attempts: int = Field(default=3, ge=1, le=10)
    job_lease_seconds: float = Field(default=60, gt=0)
    job_heartbeat_seconds: float = Field(default=15, gt=0)
    job_backoff_seconds: float = Field(default=5, gt=0)
    job_backoff_cap_seconds: float = Field(default=60, gt=0)
    worker_poll_seconds: float = Field(default=2, gt=0)
    worker_sweep_seconds: float = Field(default=60, gt=0)
    orphan_grace_seconds: float = Field(default=3600, ge=1)
    retrieval_candidate_k: int = Field(default=20, ge=10, le=100)
    retrieval_top_k: int = Field(default=5, ge=1, le=10)
    retrieval_score_threshold: float | None = Field(default=None, ge=-1, le=1)
    auth_token_ttl_seconds: int = Field(default=3600, ge=60, le=86400)
    demo_admin_password: SecretStr | None = None
    demo_member_password: SecretStr | None = None
    app_timezone: str = "Asia/Ho_Chi_Minh"

    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "knowledge_e5_small_v1"

    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_free_tier_confirmed: bool = False
    llm_quota_confirmed: bool = False
    llm_evidence_budget_tokens: int = Field(default=4000, ge=1, le=32000)
    llm_max_output_tokens: int = Field(default=800, ge=128, le=8192)
    llm_safety_margin_tokens: int = Field(default=256, ge=64)
    llm_context_window_tokens: int = Field(default=32768, ge=1024, le=1_048_576)
    # 60 s per provider call: the slowest held-out query took 45.5 s end to end (including eval
    # pacing), so normal calls fit with margin, while a hung call fails at ~1 min instead of 2.
    llm_call_timeout_seconds: float = Field(default=60, gt=0, le=120)
    query_timeout_seconds: float = Field(default=150, gt=0, le=150)
    llm_max_concurrency: int = Field(default=2, ge=1, le=2)
    stt_model: str = "small"

    @field_validator("retrieval_score_threshold", mode="before")
    @classmethod
    def empty_threshold(cls, value):
        return None if value == "" else value

    @model_validator(mode="after")
    def chunk_budget(self):
        if (
            self.llm_max_output_tokens + self.llm_safety_margin_tokens
            >= self.llm_context_window_tokens
        ):
            raise ValueError("LLM output and margin must fit the context window")
        if self.embedding_device != "cpu":
            raise ValueError("The frozen E5 worker profile requires CPU")
        if self.job_heartbeat_seconds * 2 >= self.job_lease_seconds:
            raise ValueError("Heartbeat must be less than half the lease")
        if self.job_backoff_seconds > self.job_backoff_cap_seconds:
            raise ValueError("Backoff base must not exceed cap")
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError("Chunk overlap must be smaller than the complete input budget")
        if (self.embedding_model, self.embedding_revision) != (
            "intfloat/multilingual-e5-small",
            "614241f622f53c4eeff9890bdc4f31cfecc418b3",
        ):
            raise ValueError("Step 05 tokenizer supports only the frozen E5-small revision")
        return self

    @field_validator("database_url", "test_database_url")
    @classmethod
    def postgres_url(cls, value: str | None) -> str | None:
        if value is not None:
            from sqlalchemy.engine import make_url

            try:
                url = make_url(value)
                valid = (
                    url.drivername == "postgresql+psycopg"
                    and bool(url.host)
                    and bool(url.database)
                    and bool(url.username)
                )
            except Exception:
                valid = False
            if not valid:
                raise ValueError("Expected an explicit PostgreSQL/psycopg connection URL")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
