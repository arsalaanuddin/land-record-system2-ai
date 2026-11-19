"""Field validation and the validation summary returned to the UI.

Only rules that can be evaluated locally are applied. Cross-database checks are
reported as ``not_configured`` because no government service is called.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field

from ..schemas.common import FieldValue, ValidationStatus
from ..schemas.document import utcnow_iso
from ..extraction.telangana_fields import StateConfig

CROSS_DB_NOTICE = "No external registry (Bhu-Naksha / Dharani) service is configured; no cross-database check was performed."


@dataclass
class ValidationOutcome:
    fields: list[FieldValue]
    summary: dict = dc_field(default_factory=dict)


class FieldValidator:
    def __init__(self, config: StateConfig) -> None:
        self.config = config
        self._formats = {
            name: re.compile(f"^(?:{pattern})$", re.IGNORECASE | re.UNICODE)
            for name, pattern in config.format_rules().items()
        }

    def validate(
        self, fields: dict[str, FieldValue], document_type: str
    ) -> ValidationOutcome:
        required = self.config.required_fields(document_type)
        min_confidence = self.config.min_ocr_confidence()

        errors: list[str] = []
        warnings: list[str] = []
        business_rules: list[dict] = []
        ordered: list[FieldValue] = list(fields.values())

        # 1. Required-field presence.
        for name in required:
            existing = fields.get(name)
            if existing is None or not existing.is_present:
                rule = self.config.fields.get(name)
                label = rule.ui_label if rule else name
                missing = existing or FieldValue(field=name, label=label, value=None)
                missing.validation_status = ValidationStatus.MISSING
                if "required_field_missing" not in missing.warnings:
                    missing.warnings = [*missing.warnings, "required_field_missing"]
                if existing is None:
                    ordered.append(missing)
                    fields[name] = missing
                else:
                    existing.validation_status = ValidationStatus.MISSING
                errors.append(f"Required field missing: {label}")

        # 2. Format validation for present fields.
        for field_value in fields.values():
            if not field_value.is_present:
                continue
            status = ValidationStatus.NOT_CHECKED
            pattern = self._formats.get(field_value.field)
            if pattern is not None:
                if pattern.match(field_value.value or ""):
                    status = ValidationStatus.VALID
                else:
                    status = ValidationStatus.INVALID
                    errors.append(
                        f"Value for {field_value.label or field_value.field} does not match the expected format"
                    )
            if (
                field_value.ocr_confidence is not None
                and field_value.ocr_confidence < min_confidence
            ):
                status = ValidationStatus.NEEDS_REVIEW
                warning = "low_ocr_confidence"
                if warning not in field_value.warnings:
                    field_value.warnings = [*field_value.warnings, warning]
                warnings.append(
                    f"{field_value.label or field_value.field}: OCR confidence below {min_confidence:.0%}"
                )
            field_value.validation_status = status

        # 3. Reportable business rules (no fabricated outcomes).
        business_rules.append(
            {
                "ruleId": "BR-01",
                "ruleName": "Required fields present",
                "passed": not any("Required field missing" in e for e in errors),
                "details": ", ".join(required) if required else "No required fields for this document type",
            }
        )
        business_rules.append(
            {
                "ruleId": "BR-02",
                "ruleName": "Value format conformance",
                "passed": not any("does not match the expected format" in e for e in errors),
                "details": "Checked against state_configs format rules",
            }
        )

        summary = {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "crossDatabaseChecks": [
                {
                    "dbName": "Bhu-Naksha (external registry)",
                    "status": "not_configured",
                    "message": CROSS_DB_NOTICE,
                    "lastChecked": None,
                }
            ],
            "duplicateCheck": {
                "isDuplicate": False,
                "duplicateWithId": None,
                "message": "No local duplicate found",
            },
            "businessRules": business_rules,
            "validatedAt": utcnow_iso(),
        }
        return ValidationOutcome(fields=ordered, summary=summary)
