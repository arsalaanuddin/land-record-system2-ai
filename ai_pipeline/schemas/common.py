"""Shared value objects for extraction output.

The field object defined here is the contract every stage must respect:
a value is only ever present when it was actually read off the document.
Missing or unreadable data stays ``None`` and is flagged, never guessed.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class ValidationStatus(str, Enum):
    VALID = "valid"
    INVALID = "invalid"
    MISSING = "missing"
    UNREADABLE = "unreadable"
    NEEDS_REVIEW = "needs_review"
    NOT_CHECKED = "not_checked"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    FLAGGED = "flagged"


class ExtractionMethod(str, Enum):
    RULES = "rules"
    LAYOUTLM = "layoutlm"
    MANUAL = "manual"
    NONE = "none"


class ContentType(str, Enum):
    PRINTED = "printed"
    HANDWRITTEN = "handwritten"
    MIXED = "mixed"
    UNCERTAIN = "uncertain"


class BBox(BaseModel):
    """Axis-aligned box in source-image pixels."""

    x: float
    y: float
    width: float
    height: float

    def as_tuple(self) -> tuple[float, float, float, float]:
        return (self.x, self.y, self.x + self.width, self.y + self.height)


class SourceRef(BaseModel):
    page: int = Field(ge=1, description="1-based page number in the uploaded document")
    bbox: Optional[BBox] = None
    region_id: Optional[str] = None


class FieldValue(BaseModel):
    """One semantic field read from a document.

    ``ocr_confidence`` is the OCR engine's own score (0..1) for the text the
    value came from. ``extraction_confidence`` is the strength of the rule/model
    match that mapped that text to this field (0..1). Neither is ever estimated
    from the other, and both stay ``None`` when nothing was read.
    """

    field: str
    label: Optional[str] = None
    value: Optional[str] = None
    original_text: Optional[str] = None
    value_type: str = "text"
    ocr_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    extraction_confidence: Optional[float] = Field(default=None, ge=0, le=1)
    extraction_method: ExtractionMethod = ExtractionMethod.NONE
    validation_status: ValidationStatus = ValidationStatus.NOT_CHECKED
    verification_status: VerificationStatus = VerificationStatus.PENDING
    source: Optional[SourceRef] = None
    warnings: list[str] = Field(default_factory=list)

    @property
    def is_present(self) -> bool:
        return self.value is not None and self.value.strip() != ""


class OcrLine(BaseModel):
    """A single recognised text line with its geometry."""

    text: str
    confidence: Optional[float] = None
    page: int = 1
    bbox: Optional[BBox] = None

    def normalised(self) -> str:
        return " ".join(self.text.split())


def to_jsonable(value: Any) -> Any:
    """Serialise pydantic models/enums as plain JSON-safe structures."""
    if isinstance(value, BaseModel):
        dumper = getattr(value, "model_dump", None) or value.dict
        return dumper(mode="json") if getattr(value, "model_dump", None) else dumper()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [to_jsonable(v) for v in value]
    return value
