"""Aggregate extraction result for one document."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from .common import ExtractionMethod, FieldValue


class ExtractionResult(BaseModel):
    document_id: str
    document_type: str = "unknown"
    language: Optional[str] = None
    page_count: int = 0
    fields: list[FieldValue] = Field(default_factory=list)
    extraction_method: ExtractionMethod = ExtractionMethod.NONE
    ocr_engine: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)

    def by_name(self, name: str) -> Optional[FieldValue]:
        for field in self.fields:
            if field.field == name:
                return field
        return None

    def summary(self) -> dict:
        """Flat convenience view used for list endpoints.

        Missing values are returned as ``None`` so callers can render a dash
        rather than inventing a placeholder such as a sample name.
        """
        wanted = {
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
        out: dict = {}
        for field_name, key in wanted.items():
            field = self.by_name(field_name)
            out[key] = field.value if field and field.value else None
        return out
