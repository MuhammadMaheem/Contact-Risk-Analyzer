from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Contract & Legal Document Risk Analyzer"
    environment: str = "development"

    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'app.db'}"

    jwt_secret_key: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    groq_api_key: str = ""
    groq_extraction_model: str = "llama-3.3-70b-versatile"
    groq_risk_model: str = "llama-3.3-70b-versatile"
    groq_summary_model: str = "llama-3.1-8b-instant"
    groq_rag_model: str = "llama-3.1-8b-instant"

    embedding_model_name: str = "all-MiniLM-L6-v2"

    upload_dir: Path = BASE_DIR / "uploads"
    chroma_dir: Path = BASE_DIR / "storage" / "chroma"
    reports_dir: Path = BASE_DIR / "storage" / "generated_reports"

    max_upload_size_mb: int = 20
    allowed_extensions: tuple[str, ...] = (".pdf", ".docx", ".txt")

    admin_email: str = "admin@example.com"
    admin_password: str = "ChangeMe123!"
    admin_full_name: str = "System Administrator"

    cors_origins: list[str] = ["http://localhost:3000"]

    stale_processing_minutes: int = 10


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings
