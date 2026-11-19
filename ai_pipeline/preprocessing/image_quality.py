"""Measured image-quality metrics used to route scans to human review."""

from __future__ import annotations

from pathlib import Path

from .image_preprocessor import PreprocessError, load_image


def assess_image_quality(image_path: Path) -> dict:
    """Return blur/contrast/resolution metrics for one page.

    The status is derived from measured thresholds, not from a fixed guess.
    """
    cv2 = None
    try:
        import cv2  # type: ignore
    except ImportError:  # pragma: no cover
        cv2 = None

    image = load_image(image_path)
    height, width = image.shape[:2]

    if cv2 is None:  # pragma: no cover - cv2 is required by load_image
        raise PreprocessError("OpenCV is not installed; quality assessment is unavailable.")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    contrast = float(gray.std())
    min_dimension = min(width, height)

    warnings: list[str] = []
    if blur_score < 60:
        warnings.append("low_sharpness")
    if contrast < 25:
        warnings.append("low_contrast")
    if min_dimension < 800:
        warnings.append("low_resolution")
    if max(width, height) < 1200:
        warnings.append("low_dpi")

    if warnings:
        status = "poor" if len(warnings) >= 2 else "fair"
    else:
        status = "good"

    return {
        "width": int(width),
        "height": int(height),
        "blur_score": round(blur_score, 2),
        "contrast": round(contrast, 2),
        "status": status,
        "warnings": warnings,
    }
