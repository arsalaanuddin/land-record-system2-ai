from ai_pipeline.services.record_view import field_to_view, summary_from_fields, to_record_view


def test_summary_uses_camel_case_keys_from_stored_fields():
    fields = [
        {"field": "survey_number", "value": "142/A", "label": "Survey"},
        {"field": "owner_name", "value": "Ramesh Kumar", "label": "Owner"},
        {"field": "area", "value": None, "label": "Area"},
    ]
    summary = summary_from_fields(fields)
    assert summary == {"surveyNumber": "142/A", "ownerName": "Ramesh Kumar"}


def test_field_view_keeps_null_when_nothing_was_read():
    view = field_to_view(
        {
            "field": "owner_name",
            "label": "Owner",
            "value": None,
            "original_text": None,
            "ocr_confidence": None,
            "extraction_confidence": None,
            "validation_status": "missing",
            "source": {"page": 1, "bbox": None},
            "warnings": ["required_field_missing"],
        }
    )
    assert view["value"] is None
    assert view["confidence"] is None
    assert view["original_text"] is None
    assert view["validation_status"] == "missing"


def test_record_view_maps_stored_summary():
    document = {
        "id": "LRD-1",
        "status": "verified",
        "summary": {"surveyNumber": "142/A"},
        "validation": {"passed": True},
        "overall_confidence": 0.91,
        "sha256": "abc",
        "created_at": "2026-01-01T00:00:00+00:00",
        "updated_at": "2026-01-01T00:00:00+00:00",
    }
    view = to_record_view(document, [])
    assert view["surveyNumber"] == "142/A"
    assert view["status"] == "verified"
    assert round(view["confidenceScore"], 1) == 91.0
    assert view["ownerName"] is None
