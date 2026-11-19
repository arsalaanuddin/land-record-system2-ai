"""OCR engine and result-normalisation tests."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ai_pipeline.ocr.printed_ocr import PaddlePrintedOCR, normalise_paddle_result

FIXTURE = Path(__file__).parent / "fixtures" / "telugu_printed_sample.png"
TELUGU = re.compile(r"[\u0C00-\u0C7F]")


def test_normalises_paddle3_payload() -> None:
    """PaddleOCR 3.x nests recognitions under a ``res`` key."""
    raw = [
        {
            "res": {
                "rec_texts": ["సర్వే నంబర్ 142/బి", ""],
                "rec_scores": [0.99, 0.4],
                "rec_polys": [[[1, 2], [30, 2], [30, 12], [1, 12]], [[0, 0], [1, 1], [1, 1], [0, 0]]],
            }
        }
    ]
    lines = normalise_paddle_result(raw, page_number=1)
    assert [line.text for line in lines] == ["సర్వే నంబర్ 142/బి"]
    assert lines[0].confidence == pytest.approx(0.99)
    assert lines[0].bbox is not None and lines[0].bbox.width == pytest.approx(29)
    assert lines[0].page == 1


def test_engine_returns_telugu_text() -> None:
    """The real engine must read Telugu glyphs from a printed fixture."""
    if not Path(FIXTURE).exists():
        pytest.skip("Telugu OCR fixture missing")

    engine = PaddlePrintedOCR(lang="te")
    if not engine.is_available():
        pytest.skip(f"PaddleOCR unavailable: {engine.load_error}")

    lines = engine.recognise_page(FIXTURE, page_number=1)
    assert lines, "engine returned no OCR lines"

    text = "\n".join(line.text for line in lines)
    assert TELUGU.search(text), f"no Telugu script recognised: {text!r}"
    assert "142" in text, f"survey number not recognised: {text!r}"

    for line in lines:
        assert line.confidence is None or 0.0 <= line.confidence <= 1.0
        assert line.bbox is not None
