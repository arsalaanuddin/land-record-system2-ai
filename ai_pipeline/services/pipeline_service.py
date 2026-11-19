"""Staged document pipeline.

Each stage records its own status, timing and message. Failures are isolated and
reported; a stage that cannot run (missing PyMuPDF/OpenCV/PaddleOCR) is marked
``unavailable`` and the document is routed to human review instead of receiving
invented output.
"""

from __future__ import annotations

import statistics
from pathlib import Path
from typing import Optional

from ..config import settings
from ..database import repository as repo
from ..extraction.field_extractor import (
    RuleBasedFieldExtractor,
    classify_document_type_by_keywords,
)
from ..extraction.telangana_fields import ConfigError, load_state_config
from ..ocr.printed_ocr import OcrExecutionError, OcrUnavailable, PaddlePrintedOCR
from ..preprocessing.image_preprocessor import PreprocessError, PreprocessStrategy, load_image, preprocess, save_image
from ..preprocessing.image_quality import assess_image_quality
from ..preprocessing.pdf_processor import (
    PdfEngineUnavailable,
    PdfProcessingError,
    is_pdf,
    render_pdf_pages,
)
from ..schemas.common import OcrLine, to_jsonable
from ..schemas.document import DocumentStatus, StageResult, StageStatus, utcnow_iso
from ..validation.field_validator import FieldValidator
from . import storage_service
from .record_view import summary_from_fields

STAGE_ORDER = [
    ("pdf_render", "Document ingestion and page rendering"),
    ("preprocess", "Image preprocessing and quality assessment"),
    ("ocr", "Printed-text OCR"),
    ("field_extraction", "Semantic field extraction"),
    ("validation", "Field validation"),
]


class PipelineService:
    def __init__(self) -> None:
        self.config = load_state_config(settings.state_config_dir)
        self.extractor = RuleBasedFieldExtractor(self.config)
        self.validator = FieldValidator(self.config)
        self.ocr = PaddlePrintedOCR(lang=settings.paddle_language, enabled=settings.enable_paddle)

    # ------------------------------------------------------------------ helpers
    def _stages(self) -> dict[str, StageResult]:
        return {name: StageResult(name=name) for name, _ in STAGE_ORDER}

    def _persist_stages(self, document_id: str, stages: dict[str, StageResult], status: Optional[str] = None,
                        warnings: Optional[list[str]] = None) -> None:
        values = {"stages": [to_jsonable(stage) for stage in stages.values()]}
        if status:
            values["status"] = status
        if warnings is not None:
            values["warnings"] = warnings
        repo.update_document(document_id, **values)

    def _begin(self, stages: dict[str, StageResult], name: str) -> StageResult:
        stage = stages[name]
        stage.status = StageStatus.RUNNING
        stage.started_at = utcnow_iso()
        return stage

    def _finish(self, stage: StageResult, status: StageStatus, message: Optional[str] = None,
                details: Optional[dict] = None) -> None:
        stage.status = status
        stage.finished_at = utcnow_iso()
        stage.message = message
        stage.details = details or {}

    # --------------------------------------------------------------------- run
    def run(self, document_id: str, enable_denoise: bool = True) -> None:
        document = repo.get_document(document_id)
        if document is None:
            return

        stages = self._stages()
        warnings: list[str] = list(document.get("warnings") or [])

        try:
            pages = self._stage_render(document, stages, warnings)
            self._persist_stages(document_id, stages, DocumentStatus.PROCESSING.value)

            processed_pages = self._stage_preprocess(
                document_id, pages, stages, warnings, enable_denoise=enable_denoise
            )

            lines = self._stage_ocr(document_id, processed_pages, stages, warnings)

            # Persist pages once OCR lines (and therefore bbox references) exist.
            repo.add_pages(
                document_id,
                [
                    {
                        "page_number": page["page_number"],
                        "image_path": page["image_path"],
                        "width": page["width"],
                        "height": page["height"],
                        "quality": page.get("quality", {}),
                        "ocr_lines": page.get("ocr_lines", []),
                    }
                    for page in processed_pages
                ],
            )

            fields, document_type = self._stage_extract(lines, document, stages, warnings)
            status = self._stage_validate(document_id, fields, document_type, lines, stages, warnings)
            self._persist_stages(document_id, stages, status, warnings)
        except Exception as exc:  # noqa: BLE001 - surfaced as a failed stage
            for stage in stages.values():
                if stage.status in (StageStatus.PENDING, StageStatus.RUNNING):
                    self._finish(stage, StageStatus.SKIPPED, "Aborted after an earlier stage failed")
            warnings.append(f"pipeline_error: {exc}")
            repo.update_document(
                document_id,
                status=DocumentStatus.FAILED.value,
                warnings=warnings,
                stages=[to_jsonable(stage) for stage in stages.values()],
            )

    # ------------------------------------------------------------------ stages
    def _stage_render(self, document: dict, stages: dict[str, StageResult], warnings: list[str]) -> list[dict]:
        stage = self._begin(stages, "pdf_render")
        source = storage_service.resolve_path(document["stored_path"])
        page_output_dir = storage_service.document_page_dir(document["id"])

        try:
            if is_pdf(source):
                rendered = render_pdf_pages(source, page_output_dir, dpi=settings.pdf_dpi)
                pages = [
                    {
                        "page_number": item.page_number,
                        "source_path": item.image_path,
                        "image_path": item.image_path,
                        "width": item.width,
                        "height": item.height,
                        "quality": {},
                    }
                    for item in rendered
                ]
            else:
                image = load_image(source)
                target = storage_service.copy_as_page(source, document["id"], 1)
                height, width = image.shape[:2]
                pages = [
                    {
                        "page_number": 1,
                        "source_path": target,
                        "image_path": target,
                        "width": int(width),
                        "height": int(height),
                        "quality": {},
                    }
                ]
        except PdfEngineUnavailable as exc:
            self._finish(stage, StageStatus.UNAVAILABLE, str(exc))
            warnings.append("pdf_engine_unavailable")
            self._persist_stages(document["id"], stages, DocumentStatus.FAILED.value, warnings)
            raise
        except (PdfProcessingError, PreprocessError) as exc:
            self._finish(stage, StageStatus.FAILED, str(exc))
            warnings.append(f"page_render_failed: {exc}")
            self._persist_stages(document["id"], stages, DocumentStatus.FAILED.value, warnings)
            raise

        self._finish(
            stage,
            StageStatus.COMPLETED,
            f"Rendered {len(pages)} page(s)",
            {"pages": len(pages), "dpi": settings.pdf_dpi},
        )
        repo.update_document(document["id"], total_pages=len(pages))
        document["total_pages"] = len(pages)
        return pages

    def _stage_preprocess(
        self,
        document_id: str,
        pages: list[dict],
        stages: dict[str, StageResult],
        warnings: list[str],
        enable_denoise: bool = True,
    ) -> list[dict]:
        stage = self._begin(stages, "preprocess")
        derived_dir = storage_service.document_page_dir(document_id) / "derived"
        processed: list[dict] = []
        failures = 0

        for page in pages:
            quality = {}
            try:
                quality = assess_image_quality(Path(page["source_path"]))
            except Exception as exc:  # noqa: BLE001 - quality is advisory
                warnings.append(f"quality_assessment_failed_page_{page['page_number']}: {exc}")

            image_path = Path(page["source_path"])
            try:
                image = load_image(image_path)
                enhanced, angle = preprocess(
                    image, PreprocessStrategy.PRINTED, denoise=enable_denoise
                )
                target = derived_dir / f"page-{page['page_number']:04d}.png"
                save_image(target, enhanced)
                image_path = target
                quality["skew_angle_degrees"] = round(angle, 2)
            except PreprocessError as exc:
                failures += 1
                warnings.append(f"preprocess_unavailable_page_{page['page_number']}: {exc}")

            if quality.get("warnings"):
                warnings.extend(f"page_{page['page_number']}_{w}" for w in quality["warnings"])

            processed.append(
                {
                    **page,
                    "image_path": storage_service.relative_path(image_path),
                    "quality": quality,
                    "ocr_lines": [],
                }
            )

        if failures and failures == len(pages):
            self._finish(
                stage,
                StageStatus.UNAVAILABLE,
                "OpenCV preprocessing unavailable; using original pages",
                {"denoise": enable_denoise},
            )
        else:
            self._finish(
                stage,
                StageStatus.COMPLETED,
                f"Preprocessed {len(pages) - failures}/{len(pages)} page(s)"
                + ("" if enable_denoise else " without denoising (disabled for this upload)"),
                {"preprocessed": len(pages) - failures, "failed": failures, "denoise": enable_denoise},
            )
        return processed

    def _stage_ocr(
        self, document_id: str, pages: list[dict], stages: dict[str, StageResult], warnings: list[str]
    ) -> list[OcrLine]:
        stage = self._begin(stages, "ocr")
        if not self.ocr.is_available():
            reason = self.ocr.load_error or "OCR engine unavailable"
            self._finish(stage, StageStatus.UNAVAILABLE, reason, self.ocr.describe())
            warnings.append("ocr_engine_unavailable")
            return []

        all_lines: list[OcrLine] = []
        page_failures = 0
        for page in pages:
            image_path = storage_service.resolve_path(page["image_path"])
            try:
                lines = self.ocr.recognise_page(image_path, page["page_number"])
            except (OcrUnavailable, OcrExecutionError) as exc:
                page_failures += 1
                warnings.append(f"ocr_failed_page_{page['page_number']}: {exc}")
                continue
            page["ocr_lines"] = [to_jsonable(line) for line in lines]
            all_lines.extend(lines)

        if page_failures == len(pages) and pages:
            self._finish(stage, StageStatus.FAILED, "OCR failed on every page")
        else:
            average = (
                statistics.mean([l.confidence for l in all_lines if l.confidence is not None])
                if any(l.confidence is not None for l in all_lines)
                else None
            )
            self._finish(
                stage,
                StageStatus.COMPLETED,
                f"Recognised {len(all_lines)} line(s) across {len(pages)} page(s)",
                {
                    **self.ocr.describe(),
                    "lines": len(all_lines),
                    "averageConfidence": None if average is None else round(float(average), 4),
                    "pageFailures": page_failures,
                },
            )
        return all_lines

    def _stage_extract(
        self, lines: list[OcrLine], document: dict, stages: dict[str, StageResult], warnings: list[str]
    ) -> tuple[dict, str]:
        stage = self._begin(stages, "field_extraction")
        full_text = "\n".join(line.normalised() for line in lines)

        declared = (document.get("declared_document_type") or "").strip()
        method = "declared"
        document_type: Optional[str] = None
        if declared in self.config.document_types:
            document_type = declared
        else:
            document_type, score = classify_document_type_by_keywords(full_text, self.config)
            method = "keyword_rules" if document_type else "none"
            if document_type and score:
                warnings.append(
                    f"document_type_inferred_by_keywords:{score:.2f} (no trained classifier yet)"
                )

        if not document_type:
            document_type = "other" if full_text else "unknown"
            method = "none"

        fields = self.extractor.extract(lines)
        self._finish(
            stage,
            StageStatus.COMPLETED,
            f"Extracted {len(fields)} field(s) using rule-based matching",
            {
                "fields": len(fields),
                "method": "rules",
                "documentType": document_type,
                "documentTypeMethod": method,
            },
        )
        repo.update_document(
            document["id"],
            document_type=document_type,
            extraction_method="rules" if fields else "none",
        )
        return fields, document_type

    def _stage_validate(
        self,
        document_id: str,
        fields: dict,
        document_type: str,
        lines: list[OcrLine],
        stages: dict[str, StageResult],
        warnings: list[str],
    ) -> str:
        stage = self._begin(stages, "validation")
        outcome = self.validator.validate(fields, document_type)
        field_dicts = [to_jsonable(field) for field in outcome.fields]

        summary = summary_from_fields(field_dicts)

        # Local duplicate detection on survey number only.
        survey = summary.get("surveyNumber")
        duplicate_id = repo.find_duplicate_survey(survey, exclude_id=document_id) if survey else None
        outcome.summary["duplicateCheck"] = {
            "isDuplicate": bool(duplicate_id),
            "duplicateWithId": duplicate_id,
            "message": (
                f"Survey number already present in record {duplicate_id}"
                if duplicate_id
                else ("No duplicate survey number in the local database" if survey else "Survey number not available")
            ),
        }
        if duplicate_id:
            warnings.append(f"duplicate_survey_number:{duplicate_id}")

        confidence = (
            statistics.mean([l.confidence for l in lines if l.confidence is not None])
            if any(l.confidence is not None for l in lines)
            else None
        )

        repo.replace_fields(document_id, field_dicts)

        passed = bool(outcome.summary.get("passed")) and bool(lines)
        status = DocumentStatus.PROCESSED.value if passed else DocumentStatus.NEEDS_REVIEW.value

        repo.update_document(
            document_id,
            summary=summary,
            validation=outcome.summary,
            overall_confidence=None if confidence is None else round(float(confidence), 4),
            status=status,
            warnings=warnings,
        )

        details = {
            "fields": len(field_dicts),
            "errors": len(outcome.summary.get("errors", [])),
            "warnings": len(outcome.summary.get("warnings", [])),
            "passed": passed,
        }
        self._finish(stage, StageStatus.COMPLETED, "Validation complete", details)
        # Field values are persisted separately; keep the stage view small.
        stages["validation"].details = details
        return status


def run_pipeline(document_id: str, enable_denoise: bool = True) -> None:
    """Entry point used by FastAPI background tasks."""
    try:
        PipelineService().run(document_id, enable_denoise=enable_denoise)
    except ConfigError as exc:
        repo.update_document(
            document_id,
            status=DocumentStatus.FAILED.value,
            warnings=[*((repo.get_document(document_id) or {}).get("warnings") or []), f"config_error: {exc}"],
        )
