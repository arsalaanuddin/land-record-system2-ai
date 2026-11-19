"""Filesystem layout for uploaded documents and rendered pages."""

from __future__ import annotations

import shutil
from pathlib import Path

from ..config import settings


def document_upload_dir(document_id: str) -> Path:
    path = settings.upload_dir / document_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def document_page_dir(document_id: str) -> Path:
    path = settings.page_dir / document_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def safe_filename(name: str) -> str:
    cleaned = Path(name).name.replace("\\", "_").strip()
    cleaned = "".join(char for char in cleaned if char.isprintable())
    return cleaned or "upload"


def save_original(contents: bytes, filename: str, document_id: str) -> Path:
    target = document_upload_dir(document_id) / safe_filename(filename)
    target.write_bytes(contents)
    return target


def copy_as_page(source: Path, document_id: str, page_number: int = 1) -> Path:
    target = document_page_dir(document_id) / f"page-{page_number:04d}.png"
    shutil.copyfile(source, target)
    return target


def relative_path(path: Path) -> str:
    """Store paths relative to the storage root so the tree can move."""
    try:
        return str(Path(path).resolve().relative_to(settings.storage_root.resolve()))
    except ValueError:
        return str(Path(path).resolve())


def resolve_path(stored: str) -> Path:
    candidate = Path(stored)
    if candidate.is_absolute():
        return candidate
    return settings.storage_root / candidate
