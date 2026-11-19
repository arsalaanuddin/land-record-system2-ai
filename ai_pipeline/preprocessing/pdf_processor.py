"""PDF → page images using PyMuPDF.

PyMuPDF is optional at runtime: when it is missing the caller receives a
``PdfEngineUnavailable`` error and must report the stage as unavailable rather
than silently continuing with no pages.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class PdfProcessingError(RuntimeError):
    pass


class PdfEngineUnavailable(PdfProcessingError):
    """Raised when PyMuPDF (fitz) cannot be imported."""


@dataclass
class RenderedPage:
    page_number: int
    image_path: Path
    width: int
    height: int


def _import_fitz():
    try:
        import fitz  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise PdfEngineUnavailable(
            "PyMuPDF is not installed; PDF rendering is unavailable. "
            "Install it with `pip install PyMuPDF`."
        ) from exc
    return fitz


def is_pdf(path: Path) -> bool:
    return path.suffix.lower() == ".pdf"


def render_pdf_pages(
    pdf_path: Path,
    output_dir: Path,
    dpi: int = 200,
    max_pages: Optional[int] = None,
) -> list[RenderedPage]:
    """Render every page (or the first ``max_pages``) to PNG.

    Raises ``PdfEngineUnavailable`` when PyMuPDF is missing and
    ``PdfProcessingError`` when the file cannot be opened.
    """
    fitz = _import_fitz()
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        document = fitz.open(str(pdf_path))
    except Exception as exc:  # noqa: BLE001 - surfaced to the stage result
        raise PdfProcessingError(f"Could not open PDF: {exc}") from exc

    pages: list[RenderedPage] = []
    try:
        total = document.page_count if max_pages is None else min(document.page_count, max_pages)
        for index in range(total):
            page = document.load_page(index)
            pix = page.get_pixmap(dpi=dpi)
            target = output_dir / f"page-{index + 1:04d}.png"
            pix.save(str(target))
            pages.append(
                RenderedPage(
                    page_number=index + 1,
                    image_path=target,
                    width=int(pix.width),
                    height=int(pix.height),
                )
            )
    finally:
        document.close()

    if not pages:
        raise PdfProcessingError("PDF contains no renderable pages")
    return pages
