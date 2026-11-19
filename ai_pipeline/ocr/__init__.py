"""OCR package."""

from .handwriting_ocr import (
    HandwritingRecognizer,
    HandwritingResult,
    UnavailableHandwritingRecognizer,
    load_recognizer,
)
from .printed_ocr import (
    OcrExecutionError,
    OcrUnavailable,
    PaddlePrintedOCR,
    normalise_paddle_result,
)

__all__ = [
    "HandwritingRecognizer",
    "HandwritingResult",
    "OcrExecutionError",
    "OcrUnavailable",
    "PaddlePrintedOCR",
    "UnavailableHandwritingRecognizer",
    "load_recognizer",
    "normalise_paddle_result",
]
