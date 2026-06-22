from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _default_dataset_csv_path() -> Path:
    """Prioriza `dataset/tickets.csv` (enunciado), luego raíz del repo y volumen Docker."""
    here = Path(__file__).resolve()
    repo_root = here.parents[3]
    candidates = [
        repo_root / "dataset" / "tickets.csv",
        repo_root / "tickets.csv",
        here.parents[2] / "data" / "tickets.csv",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def _default_knowledge_base_path() -> Path:
    backend_dir = Path(__file__).resolve().parents[2]
    return backend_dir / "knowledge_base" / "support_policies.md"


def _default_sqlite_url() -> str:
    backend_dir = Path(__file__).resolve().parents[2]
    db_path = backend_dir / "data" / "tickets.db"
    return f"sqlite+aiosqlite:///{db_path.resolve().as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    database_url: str = Field(default_factory=_default_sqlite_url)
    dataset_csv_path: Path = Field(default_factory=_default_dataset_csv_path)
    auto_seed_csv: bool = True

    knowledge_base_path: Path = Field(default_factory=_default_knowledge_base_path)

    llm_provider: Literal["mock", "openai"] = Field(
        default="mock",
        description="mock = heurísticas locales; openai = Chat Completions (requiere API key).",
    )
    openai_api_key: str | None = Field(default=None, repr=False)
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    auto_analyze_on_startup: bool = True
    analyze_startup_max: int = Field(
        default=50_000,
        ge=1,
        description="Tope de tickets a analizar al arrancar (protege coste/latencia con proveedor real).",
    )

    cors_origins: str = Field(
        default="http://127.0.0.1:5173,http://localhost:5173",
        description="Orígenes permitidos por CORS (separados por coma). Vacío desactiva CORS.",
    )

    csv_upload_max_bytes: int = Field(
        default=25_000_000,
        ge=1_000_000,
        le=100_000_000,
        description="Tamaño máximo del CSV en POST /tickets/ingest (bytes).",
    )

    ask_context_max_tickets: int = Field(
        default=48,
        ge=5,
        le=200,
        description="Máximo de tickets incluidos como contexto textual en /ask.",
    )
    ask_context_max_chars: int = Field(
        default=24_000,
        ge=4000,
        le=120_000,
        description="Tope de caracteres del bloque de tickets enviado al modelo en /ask.",
    )


def get_settings() -> Settings:
    return Settings()
