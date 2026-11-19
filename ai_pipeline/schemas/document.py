"""Document and processing-stage models."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class DocumentType(str, Enum):
    PAHANI = "pahani"
    ROR_1B = "ror_1b"
    PATTADAR_PASSBOOK = "pattadar_passbook"
    SALE_DEED = "sale_deed"
    MUTATION_REGISTER = "mutation_register"
    OTHER = "other"
    UNKNOWN = "unknown"


class DocumentStatus(str, Enum):
    UPLOADED = "uploaded"
    QUEUED = "queued"
    PROCESSING = "processing"
    PROCESSED = "processed"
    NEEDS_REVIEW = "needs_review"
    VERIFIED = "verified"
    REJECTED = "rejected"
    FAILED = "failed"


class StageStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    UNAVAILABLE = "unavailable"


class StageResult(BaseModel):
    """Outcome of one pipeline stage. Reported truthfully, including failures."""

    name: str
    status: StageStatus = StageStatus.PENDING
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    message: Optional[str] = None
    details: dict = Field(default_factory=dict)

    def duration_ms(self) -> Optional[int]:
        if not self.started_at or not self.finished_at:
            return None
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.finished_at)
        except ValueError:
            return None
        return int((end - start).total_seconds() * 1000)


class PageInfo(BaseModel):
    page_number: int = Field(ge=1)
    image_path: str
    width: int
    height: int
    quality_status: str = "not_checked"
    blur_score: Optional[float] = None
    content_type: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class DocumentRecord(BaseModel):
    id: str
    filename: str
    sha256: str
    size_bytes: int
    mime_type: Optional[str] = None
    document_type: DocumentType = DocumentType.UNKNOWN
    declared_document_type: Optional[str] = None
    state: str = "telangana"
    district: Optional[str] = None
    language: Optional[str] = None
    status: DocumentStatus = DocumentStatus.UPLOADED
    total_pages: int = 0
    created_at: str = Field(default_factory=utcnow_iso)
    updated_at: str = Field(default_factory=utcnow_iso)
    warnings: list[str] = Field(default_factory=list)
    stages: list[StageResult] = Field(default_factory=list)
