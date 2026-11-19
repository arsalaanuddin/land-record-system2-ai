"""Document API: upload, processing status, results and human verification."""

from __future__ import annotations

import hashlib
import uuid
from typing import Literal, Optional

from fastapi import APIRouter, BackgroundTasks, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..config import settings
from ..database import repository as repo
from ..schemas.common import VerificationStatus, to_jsonable
from ..schemas.document import DocumentStatus, utcnow_iso
from ..services import storage_service
from ..services.pipeline_service import run_pipeline
from ..services.record_view import summary_from_fields, to_record_view

router = APIRouter(prefix="/api/documents", tags=["documents"])


class VerificationRequest(BaseModel):
    action: Literal["approve", "review", "reject"]
    officer_id: str = Field(min_length=1, max_length=128)
    role: Literal["operator", "verifier", "tehsildar", "admin"]
    updated_fields: dict[str, str] = Field(default_factory=dict)
    remarks: Optional[str] = None


def _load_or_404(document_id: str) -> dict:
    document = repo.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=404, detail=f"Document {document_id} not found")
    return document


@router.post("/upload", status_code=202)
async def upload_document(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    declared_document_type: str = Form(""),
    language: str = Form("auto"),
    district: str = Form(""),
    state: str = Form("telangana"),
    enable_denoise: bool = Form(True),
) -> dict:
    filename = file.filename or "upload"
    suffix = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    if suffix not in settings.allowed_extensions:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{suffix or 'unknown'}'. Allowed: {', '.join(settings.allowed_extensions)}",
        )

    contents = await file.read()
    if not contents:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(contents) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413, detail=f"File exceeds the {settings.max_upload_mb} MB limit"
        )

    document_id = f"LRD-{uuid.uuid4().hex[:8].upper()}"
    sha256 = hashlib.sha256(contents).hexdigest()
    stored_path = storage_service.save_original(contents, filename, document_id)

    repo.create_document(
        id=document_id,
        filename=storage_service.safe_filename(filename),
        stored_path=storage_service.relative_path(stored_path),
        sha256=sha256,
        size_bytes=len(contents),
        mime_type=file.content_type,
        document_type="unknown",
        declared_document_type=declared_document_type or None,
        state=(state or settings.state_code).strip().lower(),
        district=district or None,
        language=None if language in ("", "auto") else language,
        status=DocumentStatus.QUEUED.value,
        summary={},
        validation={},
        warnings=[],
        stages=[],
    )

    repo.add_audit(
        record_id=document_id,
        user="system",
        role="system",
        action="UPLOAD",
        details=f"Uploaded {filename} ({len(contents)} bytes), sha256={sha256[:12]}",
        ip_address=None,
    )

    background.add_task(run_pipeline, document_id, enable_denoise)

    return {
        "documentId": document_id,
        "recordId": document_id,  # backwards-compatible key for the existing UI
        "status": DocumentStatus.QUEUED.value,
        "fileName": filename,
        "fileSize": f"{len(contents) / (1024 * 1024):.2f} MB",
        "sha256": sha256,
        "declaredDocumentType": declared_document_type or None,
    }


@router.get("")
async def list_documents(
    status: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = 200,
) -> list[dict]:
    documents = repo.list_documents(limit=min(max(limit, 1), 500), status=status, document_type=document_type)
    return [to_record_view(document, repo.get_fields(document["id"])) for document in documents]


@router.get("/{document_id}")
async def get_document(document_id: str) -> dict:
    document = _load_or_404(document_id)
    fields = repo.get_fields(document_id)
    return to_record_view(document, fields)


@router.get("/{document_id}/status")
async def get_status(document_id: str) -> dict:
    document = _load_or_404(document_id)
    return {
        "documentId": document_id,
        "status": document["status"],
        "totalPages": document["total_pages"],
        "stages": [
            {
                "name": stage.get("name"),
                "status": stage.get("status", "pending"),
                "message": stage.get("message"),
                "startedAt": stage.get("started_at"),
                "finishedAt": stage.get("finished_at"),
                "details": stage.get("details", {}),
            }
            for stage in document["stages"]
        ],
        "warnings": document["warnings"],
        "updatedAt": document["updated_at"],
    }


@router.get("/{document_id}/pages/{page_number}")
async def get_page_image(document_id: str, page_number: int) -> FileResponse:
    _load_or_404(document_id)
    pages = {page["page_number"]: page for page in repo.get_pages(document_id)}
    page = pages.get(page_number)
    if page is None:
        # Falls back to the uploaded single-image file before pages are persisted.
        document = _load_or_404(document_id)
        candidate = storage_service.resolve_path(document["stored_path"])
        if page_number != 1 or candidate.suffix.lower() != ".png":
            raise HTTPException(status_code=404, detail=f"Page {page_number} not available")
        return FileResponse(candidate)
    path = storage_service.resolve_path(page["image_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Page image missing for page {page_number}")
    return FileResponse(path)


@router.put("/{document_id}/verification")
async def submit_verification(
    document_id: str, payload: VerificationRequest, request: Request
) -> dict:
    document = _load_or_404(document_id)
    stored_fields = repo.get_fields(document_id)
    by_name = {field.get("field"): field for field in stored_fields}
    ip_address = request.client.host if request.client else None

    corrections: list[dict] = []
    for field_name, new_value in payload.updated_fields.items():
        field = by_name.get(field_name)
        if field is None:
            continue
        old_value = field.get("value")
        if old_value == new_value:
            continue
        field["value"] = new_value
        field["verification_status"] = VerificationStatus.APPROVED.value
        field["validation_status"] = "valid" if new_value else "missing"
        field["warnings"] = [*field.get("warnings", []), "human_corrected"]
        corrections.append(
            {"field": field_name, "old": old_value, "new": new_value, "label": field.get("label")}
        )

    verification_status = (
        VerificationStatus.APPROVED
        if payload.action == "approve"
        else VerificationStatus.REJECTED
        if payload.action == "reject"
        else VerificationStatus.FLAGGED
    )
    for field in stored_fields:
        if field.get("field") not in payload.updated_fields:
            field["verification_status"] = verification_status.value

    repo.replace_fields(document_id, stored_fields)

    document_status = {
        "approve": DocumentStatus.VERIFIED,
        "reject": DocumentStatus.REJECTED,
        "review": DocumentStatus.NEEDS_REVIEW,
    }[payload.action]

    summary = summary_from_fields(stored_fields)
    repo.update_document(document_id, status=document_status.value, summary=summary)

    for correction in corrections:
        repo.add_audit(
            record_id=document_id,
            user=payload.officer_id,
            role=payload.role,
            action="FIELD_EDIT",
            field_changed=correction["label"] or correction["field"],
            old_value=correction["old"],
            new_value=correction["new"],
            details=payload.remarks or "Field corrected during human verification",
            ip_address=ip_address,
        )
    repo.add_audit(
        record_id=document_id,
        user=payload.officer_id,
        role=payload.role,
        action={
            "approve": "VERIFY_APPROVE",
            "reject": "VERIFY_REJECT",
            "review": "VERIFY_FLAG",
        }[payload.action],
        old_value=document["status"],
        new_value=document_status.value,
        details=payload.remarks or "Verification decision recorded",
        ip_address=ip_address,
    )

    return {
        "success": True,
        "recordId": document_id,
        "status": document_status.value,
        "fieldsCorrected": len(corrections),
        "message": f"{len(corrections)} field correction(s) persisted; document marked {document_status.value}.",
        "updatedAt": utcnow_iso(),
    }


@router.get("/{document_id}/export")
async def export_record(document_id: str) -> dict:
    document = _load_or_404(document_id)
    return {
        "document": {
            key: value
            for key, value in document.items()
            if key not in {"stages", "summary", "validation", "warnings"}
        },
        "summary": document.get("summary"),
        "validation": document.get("validation"),
        "warnings": document.get("warnings"),
        "fields": [to_jsonable(field) for field in repo.get_fields(document_id)],
        "pages": [
            {key: value for key, value in page.items() if key != "ocr_lines"}
            for page in repo.get_pages(document_id)
        ],
    }
