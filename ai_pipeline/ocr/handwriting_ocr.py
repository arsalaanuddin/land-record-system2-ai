"""Handwriting recognition interface.

No certified Telugu handwriting model ships with this repository, so the
default implementation never produces text. A region that cannot be recognised
stays unreadable and is routed to human review.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol


@dataclass
class HandwritingResult:
    recognized: bool
    text: Optional[str] = None
    confidence: Optional[float] = None
    reason: Optional[str] = None
    model_id: Optional[str] = None


class HandwritingRecognizer(Protocol):
    """Contract any handwriting backend must satisfy."""

    model_id: str

    def is_available(self) -> bool: ...

    def recognise(self, crop_path: Path) -> HandwritingResult: ...


class UnavailableHandwritingRecognizer:
    """Explicit placeholder: reports unavailability instead of guessing."""

    model_id = "none"
    reason = (
        "No Telugu handwriting recogniser is installed. This region requires "
        "human transcription."
    )

    def is_available(self) -> bool:
        return False

    def recognise(self, crop_path: Path) -> HandwritingResult:  # noqa: ARG002 - interface
        return HandwritingResult(recognized=False, reason=self.reason, model_id=self.model_id)


def load_recognizer(model_path: Optional[Path]) -> HandwritingRecognizer:
    """Load a configured recogniser, or the honest unavailable placeholder."""
    if model_path is None or not model_path.exists():
        return UnavailableHandwritingRecognizer()
    # A trained checkpoint loader is added when training data exists; until then
    # an unrecognised file must not be treated as a working model.
    return UnavailableHandwritingRecognizer()
