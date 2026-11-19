from ai_pipeline.config import settings
from ai_pipeline.extraction import RuleBasedFieldExtractor, load_state_config
from ai_pipeline.schemas import BBox, OcrLine
from ai_pipeline.validation import FieldValidator


def _config():
    return load_state_config(settings.state_config_dir)


def test_inline_match_records_bbox_and_original_text():
    extractor = RuleBasedFieldExtractor(_config())
    lines = [
        OcrLine(
            text="Survey No: 142/A",
            confidence=0.93,
            page=1,
            bbox=BBox(x=10, y=20, width=200, height=30),
        )
    ]
    fields = extractor.extract(lines)
    assert "survey_number" in fields
    field = fields["survey_number"]
    assert field.value == "142/A"
    assert field.original_text == "Survey No: 142/A"
    assert field.ocr_confidence == 0.93
    assert field.source is not None and field.source.page == 1
    assert field.source.bbox.width == 200


def test_absent_field_is_not_invented():
    extractor = RuleBasedFieldExtractor(_config())
    fields = extractor.extract([OcrLine(text="Village: Ibrahimpatnam", confidence=0.8)])
    assert "owner_name" not in fields
    assert "survey_number" not in fields


def test_adjacent_label_and_value_are_paired():
    extractor = RuleBasedFieldExtractor(_config())
    lines = [
        OcrLine(text="Extent", confidence=0.8),
        OcrLine(text="2.50 acres", confidence=0.85),
    ]
    fields = extractor.extract(lines)
    assert fields["area"].value.startswith("2.50")
    assert "value_from_adjacent_line" in fields["area"].warnings


def test_validator_flags_missing_required_fields():
    validator = FieldValidator(_config())
    outcome = validator.validate({}, "pahani")
    names = {field.field for field in outcome.fields}
    assert {"survey_number", "owner_name", "area", "village"} <= names
    assert outcome.summary["passed"] is False
    assert any("Required field missing" in error for error in outcome.summary["errors"])
    assert outcome.summary["crossDatabaseChecks"][0]["status"] == "not_configured"
