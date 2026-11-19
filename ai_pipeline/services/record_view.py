"""Builds the JSON record shape consumed by the frontend.

The view exposes the spec-mandated field keys (``value``, ``original_text``,
``ocr_confidence``, ``extraction_confidence``, ``validation_status``,
``verification_status``, ``source``, ``warnings``) plus UI conveniences that are
derived from them, never invented.
"""

from __future__ import annotations

from typing import Optional

SUMMARY_FIELD_MAP = {
    "survey_number": "surveyNumber",
    "khasra_number": "khasraNumber",
    "khata_number": "khataNumber",
    "owner_name": "ownerName",
    "area": "area",
    "village": "village",
    "mandal": "tehsil",
    "district": "district",
    "land_classification": "landClassification",
    "mutation_number": "mutationNumber",
    "registration_number": "registrationDeedNo",
}


def summary_from_fields(fields: list[dict]) -> dict:
    """Map stored field payloads to the camelCase summary used by the API/DB."""
    summary: dict = {}
    for field in fields:
        key = SUMMARY_FIELD_MAP.get(field.get("field", ""))
        if key and field.get("value"):
            summary[key] = field["value"]
    return summary


STATUS_FOR_UI = {
    "uploaded": "processing",
    "queued": "processing",
    "processing": "processing",
    "processed": "review",
    "needs_review": "review",
    "verified": "verified",
    "rejected": "rejected",
    "failed": "failed",
}


def _bbox_dict(bbox: Optional[dict]) -> Optional[dict]:
    if not bbox:
        return None
    return {
        "x": bbox.get("x", 0),
        "y": bbox.get("y", 0),
        "width": bbox.get("width", 0),
        "height": bbox.get("height", 0),
    }


def field_to_view(field: dict) -> dict:
    ocr = field.get("ocr_confidence")
    source = field.get("source") or {}
    bbox = source.get("bbox")
    return {
        # spec contract
        "field": field.get("field"),
        "value": field.get("value"),
        "original_text": field.get("original_text"),
        "ocr_confidence": ocr,
        "extraction_confidence": field.get("extraction_confidence"),
        "validation_status": field.get("validation_status", "not_checked"),
        "verification_status": field.get("verification_status", "pending"),
        "extraction_method": field.get("extraction_method", "none"),
        "source": {"page": source.get("page", 1), "bbox": _bbox_dict(bbox)},
        "warnings": field.get("warnings", []),
        # UI conveniences (derived, nullable)
        "key": field.get("field"),
        "label": field.get("label") or field.get("field"),
        "category": field.get("category", "core"),
        "confidence": None if ocr is None else round(float(ocr) * 100, 1),
        "boundingBox": _bbox_dict(bbox),
    }


def to_record_view(document: dict, fields: list[dict]) -> dict:
    summary = document.get("summary") or {}
    validation = document.get("validation") or {}
    overall = document.get("overall_confidence")
    raw_status = document.get("status", "uploaded")

    return {
        "id": document["id"],
        "status": STATUS_FOR_UI.get(raw_status, "processing"),
        "rawStatus": raw_status,
        "confidenceScore": None if overall is None else round(float(overall) * 100, 1),
        "documentType": document.get("document_type", "unknown"),
        "documentLanguage": document.get("language") or document.get("state", "telangana"),
        "state": document.get("state"),
        "district": document.get("district") or summary.get("district"),
        "sha256Hash": document.get("sha256", ""),
        "lastUpdated": document.get("updated_at"),
        "createdAt": document.get("created_at"),
        "fileName": document.get("filename"),
        "pageCount": document.get("total_pages", 0),
        "extractionMethod": document.get("extraction_method", "none"),
        # summary fields are null when nothing was read
        "surveyNumber": summary.get("surveyNumber"),
        "khasraNumber": summary.get("khasraNumber"),
        "khataNumber": summary.get("khataNumber"),
        "ownerName": summary.get("ownerName"),
        "coOwners": [],
        "ownershipType": None,
        "ownershipShare": None,
        "area": summary.get("area"),
        "village": summary.get("village"),
        "tehsil": summary.get("tehsil"),
        "landClassification": summary.get("landClassification"),
        "mutationNumber": summary.get("mutationNumber"),
        "mutationDate": None,
        "mutationType": None,
        "registrationDeedNo": summary.get("registrationDeedNo"),
        "sroOffice": None,
        "registrationDate": None,
        "stampDutyStatus": None,
        "coordinates": [],
        "fields": [field_to_view(field) for field in fields],
        "validation": {
            "passed": validation.get("passed", False),
            "errors": validation.get("errors", []),
            "warnings": validation.get("warnings", []),
            "crossDatabaseChecks": validation.get("crossDatabaseChecks", []),
            "duplicateCheck": validation.get("duplicateCheck", {"isDuplicate": False, "message": "Not checked"}),
            "businessRules": validation.get("businessRules", []),
            "validatedAt": validation.get("validatedAt"),
        },
        "stages": [
            {
                "name": stage.get("name"),
                "status": stage.get("status"),
                "message": stage.get("message"),
                "durationMs": stage.get("duration_ms"),
            }
            for stage in document.get("stages", [])
        ],
        "warnings": document.get("warnings", []),
    }
