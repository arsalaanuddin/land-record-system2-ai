"""Field extraction from OCR lines produced by the real Telugu engine.

The lines below are the literal output of ``te_PP-OCRv5_mobile_rec`` on
``fixtures/telugu_printed_sample.png`` (including its OCR noise), so the rules
are tested against recogniser output rather than hand-written clean text.
"""

from __future__ import annotations

from ai_pipeline.config import settings
from ai_pipeline.extraction.field_extractor import RuleBasedFieldExtractor
from ai_pipeline.extraction.telangana_fields import load_state_config
from ai_pipeline.schemas.common import BBox, OcrLine

OCR_LINES = [
    "పహానీ భూమి రికార్డు",
    "సర్వే నంబర్ 142/బి",
    "గ్రామం కొండాపూర్",
    "భూమి విసతర్లం 2.5 ఎకరాలు",
    "పట్టాదారు పేరు రమేష్ కుమార్",
]


def _lines() -> list[OcrLine]:
    return [
        OcrLine(text=text, confidence=0.95, page=1, bbox=BBox(x=10, y=10 * index, width=200, height=30))
        for index, text in enumerate(OCR_LINES)
    ]


def _extract() -> dict:
    extractor = RuleBasedFieldExtractor(load_state_config(settings.state_config_dir))
    return extractor.extract(_lines())


def test_survey_number_from_telugu_label_variant() -> None:
    fields = _extract()
    survey = fields["survey_number"]
    assert survey.value == "142/బి"
    assert survey.original_text == "సర్వే నంబర్ 142/బి"
    assert survey.source is not None and survey.source.page == 1


def test_area_from_trailing_unit() -> None:
    fields = _extract()
    area = fields["area"]
    assert area.value == "2.5 ఎకరాలు"
    assert "value_anchored_on_unit_not_label" in area.warnings
    assert area.extraction_confidence < 0.9


def test_name_and_village_still_extracted() -> None:
    fields = _extract()
    assert fields["village"].value == "కొండాపూర్"
    assert fields["owner_name"].value == "రమేష్ కుమార్"


def test_no_value_is_invented_for_unlabelled_text() -> None:
    fields = _extract()
    assert "khata_number" not in fields
    assert "mutation_number" not in fields
