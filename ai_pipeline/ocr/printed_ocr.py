"""Printed-text OCR built on PaddleOCR 3.x.

The engine is loaded lazily and exactly once. When PaddleOCR is not installed
the caller receives ``OcrUnavailable``; the pipeline then reports the OCR stage
as unavailable instead of inventing text.

``predict()`` returns result objects whose ``.json`` payload nests the
recognitions under ``{"res": {...}}`` with parallel ``rec_texts``,
``rec_scores`` and ``rec_polys`` lists.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

from ..schemas.common import BBox, OcrLine

_TRUTHY = {"1", "true", "yes", "on"}


def _truthy(value: Optional[str]) -> bool:
    return (value or "").strip().lower() in _TRUTHY


# oneDNN/PIR kernels crash on some CPU-only hosts (``ConvertPirAttribute2RuntimeAttribute``);
# the flag must be set before ``paddle`` is imported. Off unless explicitly enabled.
if not _truthy(os.environ.get("LRS_PADDLE_MKLDNN")):
    os.environ["FLAGS_use_mkldnn"] = "0"
# Skip the model-hoster ping on first load; it only affects startup latency.
os.environ.setdefault("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK", "True")


class OcrUnavailable(RuntimeError):
    """The OCR engine or requested language model is not installed."""


class OcrExecutionError(RuntimeError):
    """The engine ran but failed on this image."""


def _polygon_to_bbox(polygon: Any) -> Optional[BBox]:
    try:
        xs = [float(point[0]) for point in polygon]
        ys = [float(point[1]) for point in polygon]
    except (TypeError, ValueError, IndexError):
        return None
    if not xs or not ys:
        return None
    return BBox(x=min(xs), y=min(ys), width=max(xs) - min(xs), height=max(ys) - min(ys))


def _payload(block: Any) -> Optional[dict]:
    """Unwrap a PaddleOCR result object (or its JSON) into the ``res`` dict."""
    if hasattr(block, "json"):
        try:
            block = block.json
        except Exception:  # noqa: BLE001 - malformed result is skipped
            return None
    if isinstance(block, dict) and isinstance(block.get("res"), dict):
        return block["res"]
    return block if isinstance(block, dict) else None


def normalise_paddle_result(raw: Any, page_number: int) -> list[OcrLine]:
    """Normalise PaddleOCR result payloads into ``OcrLine`` objects."""
    lines: list[OcrLine] = []
    for block in raw or []:
        payload = _payload(block)
        if payload is None:
            continue
        texts = payload.get("rec_texts") or []
        scores = payload.get("rec_scores") or []
        polys = payload.get("rec_polys") or payload.get("dt_polys") or []
        for index, text in enumerate(texts):
            if not isinstance(text, str) or not text.strip():
                continue
            score = scores[index] if index < len(scores) else None
            poly = polys[index] if index < len(polys) else None
            lines.append(
                OcrLine(
                    text=text,
                    confidence=float(score) if score is not None else None,
                    page=page_number,
                    bbox=_polygon_to_bbox(poly) if poly is not None else None,
                )
            )
    return lines


class PaddlePrintedOCR:
    """Lazy wrapper around PaddleOCR's printed-text pipeline.

    Model selection is configurable so the recogniser can be replaced without
    code changes:

    * ``LRS_PADDLE_DET_MODEL`` — detection model (default ``PP-OCRv5_mobile_det``;
      the server detector crashes on this CPU-only host).
    * ``LRS_PADDLE_REC_MODEL`` — recognition model (default ``<lang>_PP-OCRv5_mobile_rec``).
    * ``LRS_PADDLE_MKLDNN`` — set ``1`` to enable oneDNN (default off).
    """

    engine_name = "paddleocr"

    def __init__(self, lang: str = "te", enabled: bool = True) -> None:
        self.lang = lang
        self.enabled = enabled
        self.det_model = os.environ.get("LRS_PADDLE_DET_MODEL", "PP-OCRv5_mobile_det").strip() or None
        self.rec_model = (
            os.environ.get("LRS_PADDLE_REC_MODEL", f"{lang}_PP-OCRv5_mobile_rec").strip() or None
        )
        self.use_mkldnn = _truthy(os.environ.get("LRS_PADDLE_MKLDNN"))
        self._engine: Any = None
        self._load_error: Optional[str] = None
        self._loaded = False

    def describe(self) -> dict:
        """Non-secret engine summary recorded in the OCR stage details."""
        return {
            "engine": self.engine_name,
            "language": self.lang,
            "detectionModel": self.det_model,
            "recognitionModel": self.rec_model,
            "mkldnn": self.use_mkldnn,
        }

    def _load(self) -> Any:
        if self._loaded:
            return self._engine
        self._loaded = True
        if not self.enabled:
            self._load_error = "PaddleOCR disabled via LRS_DISABLE_PADDLE"
            return None
        try:
            from paddleocr import PaddleOCR  # type: ignore
        except ImportError:
            self._load_error = "paddleocr is not installed"
            return None
        try:
            self._engine = PaddleOCR(
                enable_mkldnn=self.use_mkldnn,
                text_detection_model_name=self.det_model,
                text_recognition_model_name=self.rec_model,
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
        except Exception as exc:  # noqa: BLE001 - reported to the caller
            self._load_error = f"PaddleOCR failed to initialise: {exc}"
            return None
        return self._engine

    @property
    def load_error(self) -> Optional[str]:
        return self._load_error

    def is_available(self) -> bool:
        return self._load() is not None

    def recognise_page(self, image_path: Path, page_number: int = 1) -> list[OcrLine]:
        engine = self._load()
        if engine is None:
            raise OcrUnavailable(self._load_error or "OCR engine unavailable")
        try:
            raw = list(engine.predict(str(image_path)))
        except Exception as exc:  # noqa: BLE001 - reported by the stage
            raise OcrExecutionError(f"OCR failed on page {page_number}: {exc}") from exc
        return normalise_paddle_result(raw, page_number)
