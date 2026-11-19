from ai_pipeline.schemas import FieldValue, SourceRef, ValidationStatus, VerificationStatus


def test_missing_value_stays_null():
    field = FieldValue(field="owner_name", label="Owner")
    assert field.value is None
    assert field.is_present is False
    assert field.validation_status == ValidationStatus.NOT_CHECKED
    assert field.verification_status == VerificationStatus.PENDING


def test_field_keeps_original_text_and_source():
    field = FieldValue(
        field="survey_number",
        value="142/A",
        original_text="Survey No: 142/A",
        ocr_confidence=0.91,
        extraction_confidence=0.9,
        source=SourceRef(page=2),
    )
    assert field.original_text == "Survey No: 142/A"
    assert field.source.page == 2
    assert field.ocr_confidence == 0.91
    assert field.value == "142/A"
