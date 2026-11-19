"""Dashboard, audit trail, API portal, GIS and session endpoints.

Every number returned here is a database count or a stored value. Anything the
system cannot measure is returned as ``None`` and labelled accordingly rather
than being filled with a plausible-looking constant.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..database import repository as repo

router = APIRouter(prefix="/api", tags=["system"])

PROCESSED_STATES = {"processed", "needs_review", "verified", "rejected"}

WARNING_LABELS = {
    "ocr_engine_unavailable": ("OCR engine unavailable", "#d32f2f"),
    "pdf_engine_unavailable": ("PDF engine unavailable", "#d32f2f"),
    "low_sharpness": ("Low scan sharpness", "#f57f17"),
    "low_contrast": ("Low scan contrast", "#f57f17"),
    "low_resolution": ("Low scan resolution", "#f57f17"),
    "low_dpi": ("Low scan DPI", "#f57f17"),
    "required_field_missing": ("Required field missing", "#d32f2f"),
}


@router.get("/dashboard/stats")
async def dashboard_stats() -> dict:
    counts = repo.status_counts()
    by_status = counts["byStatus"]
    total = counts["total"]
    processed = sum(value for key, value in by_status.items() if key in PROCESSED_STATES)
    average = counts["averageConfidence"]

    documents = repo.list_documents(limit=500)
    warning_counts: dict[str, int] = {}
    for document in documents:
        for warning in document.get("warnings", []):
            key = warning.split(":")[0]
            if key in WARNING_LABELS:
                warning_counts[key] = warning_counts.get(key, 0) + 1

    warning_total = sum(warning_counts.values())
    error_stats = [
        {
            "type": WARNING_LABELS[key][0],
            "count": value,
            "percentage": round(value / warning_total * 100, 1) if warning_total else 0,
            "color": WARNING_LABELS[key][1],
        }
        for key, value in sorted(warning_counts.items(), key=lambda item: -item[1])
    ]

    verified = by_status.get("verified", 0)
    needs_review = by_status.get("needs_review", 0) + by_status.get("processed", 0)

    return {
        "totalDocuments": total,
        "totalProcessed": processed,
        "verifiedRecords": verified,
        "requiresReview": needs_review,
        "failedDocuments": by_status.get("failed", 0),
        "processingProgress": round(processed / total * 100, 1) if total else 0.0,
        # Not measurable without a held-out labelled set; never estimated.
        "extractionAccuracy": None,
        "accuracyNote": "No held-out Telangana evaluation set has been run, so accuracy is not reported.",
        "avgConfidenceScore": None if average is None else round(float(average) * 100, 1),
        "activeLearningRetrainedCount": 0,
        "byType": counts["byType"],
        "errorStats": error_stats,
        "stateProgress": [],
        "recentActivity": [
            {
                "id": log["id"],
                "text": f"{log['action']} on {log['recordId']}"
                + (f": {log['details']}" if log.get("details") else ""),
                "time": log["timestamp"],
                "type": "success" if log["action"] in ("VERIFY_APPROVE", "UPLOAD") else "warning",
            }
            for log in repo.list_audit(limit=8)
        ],
    }


@router.get("/audit-logs")
async def audit_logs(limit: int = 100) -> list[dict]:
    return repo.list_audit(limit=min(max(limit, 1), 500))


@router.get("/api-portal")
async def api_portal() -> dict:
    keys = repo.list_api_keys()
    return {
        "apiKeys": keys,
        "integrations": [
            {
                "name": "Bhu-Naksha (external registry)",
                "status": "not_configured",
                "endpoint": "not configured",
                "latency": "n/a",
                "lastSync": "never",
            },
            {
                "name": "Telangana Bhu Bharati / Dharani",
                "status": "not_configured",
                "endpoint": "not configured",
                "latency": "n/a",
                "lastSync": "never",
            },
            {
                "name": "SRO Registration Database",
                "status": "not_configured",
                "endpoint": "not configured",
                "latency": "n/a",
                "lastSync": "never",
            },
        ],
    }


@router.get("/gis/parcels")
async def gis_parcels() -> dict:
    """GeoJSON of stored parcel geometry. Empty until cadastral vectorisation exists."""
    return {"type": "FeatureCollection", "features": []}


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=128)
    role: Literal["operator", "verifier", "tehsildar", "admin"] = "verifier"


DESIGNATIONS = {
    "operator": "Data Entry Operator",
    "verifier": "Verification Officer",
    "tehsildar": "Tehsildar / SRO",
    "admin": "System Administrator",
}


@router.post("/auth/login")
async def login(payload: LoginRequest) -> dict:
    """Local role selection only. No identity provider is configured.

    This endpoint issues no credential: it echoes the chosen role so the UI can
    gate panels. It is not authentication and the UI labels it as such.
    """
    return {
        "username": payload.username,
        "role": payload.role,
        "name": payload.username.replace("_", " ").title(),
        "designation": DESIGNATIONS[payload.role],
        "department": "Department of Revenue, Telangana",
        "authenticated": False,
        "method": "local_session_stub",
        "notice": "Role selection only. No password verification or identity provider is configured.",
    }


@router.get("/health")
async def health() -> dict:
    from ..config import settings

    return {
        "status": "ok",
        "version": "2.0.0",
        "state": settings.state_code,
        "config": settings.describe(),
    }
