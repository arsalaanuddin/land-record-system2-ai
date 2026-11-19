"""Persistence helpers. All database access goes through this module."""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import func, select

from ..schemas.document import utcnow_iso
from .connection import session_scope
from .models import ApiKey, AuditLog, Document, DocumentPage, ExtractedField


def create_document(**values: Any) -> None:
    now = utcnow_iso()
    values.setdefault("created_at", now)
    values.setdefault("updated_at", now)
    with session_scope() as session:
        session.add(Document(**values))


def get_document(document_id: str) -> Optional[dict]:
    with session_scope() as session:
        row = session.get(Document, document_id)
        return _document_dict(row) if row else None


def list_documents(
    limit: int = 200,
    status: Optional[str] = None,
    document_type: Optional[str] = None,
) -> list[dict]:
    stmt = select(Document).order_by(Document.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Document.status == status)
    if document_type:
        stmt = stmt.where(Document.document_type == document_type)
    with session_scope() as session:
        return [_document_dict(row) for row in session.scalars(stmt).all()]


def update_document(document_id: str, **values: Any) -> None:
    values["updated_at"] = utcnow_iso()
    with session_scope() as session:
        row = session.get(Document, document_id)
        if row is None:
            raise LookupError(f"Document {document_id} does not exist")
        for key, value in values.items():
            setattr(row, key, value)


def add_pages(document_id: str, pages: list[dict]) -> None:
    with session_scope() as session:
        for page in pages:
            session.add(DocumentPage(document_id=document_id, **page))


def get_pages(document_id: str) -> list[dict]:
    stmt = (
        select(DocumentPage)
        .where(DocumentPage.document_id == document_id)
        .order_by(DocumentPage.page_number)
    )
    with session_scope() as session:
        rows = session.scalars(stmt).all()
        return [
            {
                "page_number": row.page_number,
                "image_path": row.image_path,
                "width": row.width,
                "height": row.height,
                "quality": row.quality or {},
                "ocr_lines": row.ocr_lines or [],
            }
            for row in rows
        ]


def replace_fields(document_id: str, fields: list[dict]) -> None:
    with session_scope() as session:
        session.query(ExtractedField).filter(ExtractedField.document_id == document_id).delete()
        for field in fields:
            session.add(
                ExtractedField(
                    document_id=document_id,
                    field_name=field.get("field", "unknown"),
                    value=field.get("value"),
                    payload=field,
                )
            )


def get_fields(document_id: str) -> list[dict]:
    stmt = (
        select(ExtractedField)
        .where(ExtractedField.document_id == document_id)
        .order_by(ExtractedField.id)
    )
    with session_scope() as session:
        return [row.payload or {} for row in session.scalars(stmt).all()]


def find_duplicate_survey(survey_number: str, exclude_id: Optional[str] = None) -> Optional[str]:
    """Local duplicate detection on survey number. Never an external lookup."""
    with session_scope() as session:
        stmt = select(Document).where(Document.summary["surveyNumber"].as_string() == survey_number)
        if exclude_id:
            stmt = stmt.where(Document.id != exclude_id)
        row = session.scalars(stmt.limit(1)).first()
        return row.id if row else None


def add_audit(**values: Any) -> None:
    values.setdefault("timestamp", utcnow_iso())
    with session_scope() as session:
        session.add(AuditLog(**values))


def list_audit(limit: int = 100) -> list[dict]:
    stmt = select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
    with session_scope() as session:
        return [
            {
                "id": row.id,
                "recordId": row.record_id,
                "timestamp": row.timestamp,
                "user": row.user,
                "role": row.role,
                "action": row.action,
                "fieldChanged": row.field_changed,
                "oldValue": row.old_value,
                "newValue": row.new_value,
                "details": row.details,
                "ipAddress": row.ip_address,
            }
            for row in session.scalars(stmt).all()
        ]


def status_counts() -> dict:
    with session_scope() as session:
        rows = session.execute(select(Document.status, func.count()).group_by(Document.status)).all()
        total = session.scalar(select(func.count()).select_from(Document)) or 0
        avg = session.scalar(select(func.avg(Document.overall_confidence)))
        type_rows = session.execute(
            select(Document.document_type, func.count()).group_by(Document.document_type)
        ).all()
    return {
        "byStatus": {status: count for status, count in rows},
        "byType": {doc_type: count for doc_type, count in type_rows},
        "total": int(total),
        "averageConfidence": float(avg) if avg is not None else None,
    }


def list_api_keys() -> list[dict]:
    stmt = select(ApiKey).order_by(ApiKey.created.desc())
    with session_scope() as session:
        return [
            {
                "id": row.id,
                "name": row.name,
                "prefix": row.prefix,
                "role": row.role,
                "created": row.created,
                "lastUsed": row.last_used or "Never",
            }
            for row in session.scalars(stmt).all()
        ]


def _document_dict(row: Document) -> dict:
    return {
        "id": row.id,
        "filename": row.filename,
        "stored_path": row.stored_path,
        "sha256": row.sha256,
        "size_bytes": row.size_bytes,
        "mime_type": row.mime_type,
        "document_type": row.document_type,
        "declared_document_type": row.declared_document_type,
        "state": row.state,
        "district": row.district,
        "language": row.language,
        "status": row.status,
        "total_pages": row.total_pages,
        "overall_confidence": row.overall_confidence,
        "extraction_method": row.extraction_method,
        "summary": row.summary or {},
        "validation": row.validation or {},
        "warnings": row.warnings or [],
        "stages": row.stages or [],
        "created_at": row.created_at,
        "updated_at": row.updated_at,
    }
