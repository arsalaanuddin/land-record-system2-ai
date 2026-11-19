"""OpenCV preprocessing with separate printed and handwriting strategies.

Enhancement is *not* recognition: these functions only improve legibility and
never claim to read handwriting. A handwriting-friendly output is fed to the
same OCR/handwriting stage as any other image.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

import numpy as np


class PreprocessError(RuntimeError):
    pass


class PreprocessStrategy(str, Enum):
    PRINTED = "printed"
    HANDWRITING = "handwriting"


def _cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise PreprocessError("OpenCV is not installed; image preprocessing is unavailable.") from exc
    return cv2


def load_image(path: Path) -> np.ndarray:
    cv2 = _cv2()
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise PreprocessError(f"Could not decode image: {path}")
    return image


def _to_gray(image: np.ndarray) -> np.ndarray:
    cv2 = _cv2()
    if image.ndim == 2:
        return image
    return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)


def enhance_for_printed(image: np.ndarray, denoise: bool = True) -> np.ndarray:
    """Grayscale + CLAHE + optional light denoise. Useful for typed Telugu text."""
    cv2 = _cv2()
    gray = _to_gray(image)
    if denoise:
        gray = cv2.fastNlMeansDenoising(gray, h=10)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gray)


def enhance_for_handwriting(image: np.ndarray) -> np.ndarray:
    """Bilateral filter + background subtraction + Otsu threshold.

    Tuned to preserve stroke shapes for a handwriting recogniser; it does not
    attempt to interpret the strokes.
    """
    cv2 = _cv2()
    gray = _to_gray(image)
    filtered = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    background = cv2.medianBlur(filtered, 31)
    subtracted = cv2.subtract(background, filtered)
    _, binary = cv2.threshold(subtracted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return cv2.bitwise_not(binary)


def estimate_skew_angle(gray: np.ndarray) -> float:
    """Estimate page skew in degrees from the dominant near-horizontal lines."""
    cv2 = _cv2()
    edges = cv2.Canny(gray, 50, 150, apertureSize=3)
    lines = cv2.HoughLinesP(
        edges, 1, np.pi / 180, threshold=100, minLineLength=max(80, gray.shape[1] // 4), maxLineGap=10
    )
    if lines is None:
        return 0.0

    angles: list[float] = []
    for x1, y1, x2, y2 in lines[:, 0]:
        if x2 == x1:
            continue
        angle = np.degrees(np.arctan2(float(y2 - y1), float(x2 - x1)))
        if -15 <= angle <= 15:
            angles.append(angle)
    return float(np.median(angles)) if angles else 0.0


def deskew(gray: np.ndarray, max_angle: float = 10.0) -> tuple[np.ndarray, float]:
    """Rotate the page to remove skew. Returns the image and the applied angle."""
    cv2 = _cv2()
    angle = estimate_skew_angle(gray)
    if abs(angle) < 0.3 or abs(angle) > max_angle:
        return gray, 0.0
    height, width = gray.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), angle, 1.0)
    rotated = cv2.warpAffine(
        gray,
        matrix,
        (width, height),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return rotated, angle


def preprocess(
    image: np.ndarray, strategy: PreprocessStrategy = PreprocessStrategy.PRINTED, denoise: bool = True
) -> tuple[np.ndarray, float]:
    """Apply a strategy and deskew. Returns (image, skew_angle_degrees)."""
    if strategy is PreprocessStrategy.HANDWRITING:
        enhanced = enhance_for_handwriting(image)
    else:
        enhanced = enhance_for_printed(image, denoise=denoise)
    return deskew(enhanced)


def save_image(path: Path, image: np.ndarray) -> None:
    cv2 = _cv2()
    path.parent.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(path), image):
        raise PreprocessError(f"Could not write image: {path}")
