"""Pydantic contracts shared by the API, pipeline and persistence layers."""

from .common import (
    BBox,
    ContentType,
    ExtractionMethod,
    FieldValue,
    OcrLine,
    SourceRef,
    ValidationStatus,
    VerificationStatus,
    to_jsonable,
)
from .document import (
    DocumentRecord,
    DocumentStatus,
    DocumentType,
    PageInfo,
    StageResult,
    StageStatus,
    utcnow_iso,
)
from .extraction import ExtractionResult

__all__ = [
    "BBox",
    "ContentType",
    "DocumentRecord",
    "DocumentStatus",
    "DocumentType",
    "ExtractionMethod",
    "ExtractionResult",
    "FieldValue",
    "OcrLine",
    "PageInfo",
    "SourceRef",
    "StageResult",
    "StageStatus",
    "ValidationStatus",
    "VerificationStatus",
    "to_jsonable",
    "utcnow_iso",
]
