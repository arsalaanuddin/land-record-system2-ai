"""Central configuration for the Land Record Digitization pipeline.

Every path and limit used by the application resolves from here so that no
module hardcodes storage locations, model paths or database URLs.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_ROOT = BASE_DIR.parent

DEFAULT_STORAGE_ROOT = REPO_ROOT / "storage"


def _env_path(name: str, default: Path) -> Path:
    raw = os.environ.get(name)
    return Path(raw).expanduser().resolve() if raw else default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Runtime settings, read once at import time from the environment."""

    storage_root: Path
    upload_dir: Path
    page_dir: Path
    export_dir: Path
    database_url: str
    state_code: str
    state_config_dir: Path
    max_upload_mb: int
    pdf_dpi: int
    allowed_extensions: tuple[str, ...]
    paddle_language: str
    enable_paddle: bool
    cors_origins: tuple[str, ...] = ("*",)
    extra: dict = field(default_factory=dict)

    def describe(self) -> dict:
        """Safe, non-secret summary for /api/health."""
        return {
            "storageRoot": str(self.storage_root),
            "databaseUrl": _redact_database_url(self.database_url),
            "stateCode": self.state_code,
            "maxUploadMb": self.max_upload_mb,
            "pdfDpi": self.pdf_dpi,
            "paddleLanguage": self.paddle_language,
            "paddleEnabled": self.enable_paddle,
        }


def _redact_database_url(url: str) -> str:
    """Hide credentials before a URL is echoed back over HTTP."""
    if "@" not in url:
        return url
    scheme, _, rest = url.partition("://")
    _, _, host = rest.rpartition("@")
    return f"{scheme}://***@{host}"


def load_settings() -> Settings:
    storage_root = _env_path("LRS_STORAGE_ROOT", DEFAULT_STORAGE_ROOT)
    upload_dir = storage_root / "uploads"
    page_dir = storage_root / "pages"
    export_dir = storage_root / "exports"

    for directory in (storage_root, upload_dir, page_dir, export_dir):
        directory.mkdir(parents=True, exist_ok=True)

    database_url = os.environ.get(
        "DATABASE_URL", f"sqlite:///{storage_root / 'land_records.db'}"
    )
    if database_url.startswith("postgres://"):  # SQLAlchemy needs the full driver name
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    state_code = os.environ.get("LRS_STATE", "telangana").strip().lower()
    state_config_dir = BASE_DIR / "state_configs" / state_code

    return Settings(
        storage_root=storage_root,
        upload_dir=upload_dir,
        page_dir=page_dir,
        export_dir=export_dir,
        database_url=database_url,
        state_code=state_code,
        state_config_dir=state_config_dir,
        max_upload_mb=_env_int("LRS_MAX_UPLOAD_MB", 50),
        pdf_dpi=_env_int("LRS_PDF_DPI", 200),
        allowed_extensions=(".pdf", ".png", ".jpg", ".jpeg", ".tif", ".tiff"),
        paddle_language=os.environ.get("LRS_PADDLE_LANG", "te"),
        enable_paddle=os.environ.get("LRS_DISABLE_PADDLE", "").lower()
        not in {"1", "true", "yes"},
    )


settings = load_settings()
