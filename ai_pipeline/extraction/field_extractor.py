"""Rules-based semantic field extraction.

This is deliberately *not* a language model. Each match records the label that
fired, the raw OCR line, its bbox and an explicit ``extraction_confidence``
equal to the rule-match strength. When nothing matches, no field is produced —
callers must not substitute a sample value.
"""

from __future__ import annotations

from typing import Optional

from ..schemas.common import ExtractionMethod, FieldValue, OcrLine, SourceRef
from .telangana_fields import FieldRule, StateConfig

RULES_METHOD_NOTE = "extraction_confidence is rule-match strength, not a model probability"

INLINE_WITH_SEPARATOR = 0.9
INLINE_WITHOUT_SEPARATOR = 0.75
UNIT_SUFFIX = 0.8
ADJACENT_LINE = 0.55


class RuleBasedFieldExtractor:
    def __init__(self, config: StateConfig) -> None:
        self.config = config

    def extract(self, lines: list[OcrLine]) -> dict[str, FieldValue]:
        normalised = [line.normalised() for line in lines]
        found: dict[str, FieldValue] = {}

        for rule in self.config.fields.values():
            match = (
                self._match_inline(rule, lines, normalised)
                or self._match_adjacent(rule, lines, normalised)
                or self._match_unit_suffix(rule, lines, normalised)
            )
            if match is not None:
                found[rule.name] = match
        return found

    @staticmethod
    def _build(
        rule: FieldRule,
        line: OcrLine,
        value: str,
        score: float,
        *,
        original_text: Optional[str] = None,
        warning: Optional[str] = None,
    ) -> FieldValue:
        warnings = [RULES_METHOD_NOTE] + ([warning] if warning else [])
        return FieldValue(
            field=rule.name,
            label=rule.ui_label,
            value=value,
            original_text=original_text or line.text,
            value_type=rule.value_type,
            ocr_confidence=line.confidence,
            extraction_confidence=score,
            extraction_method=ExtractionMethod.RULES,
            source=SourceRef(page=line.page, bbox=line.bbox),
            warnings=warnings,
        )

    def _match_inline(
        self, rule: FieldRule, lines: list[OcrLine], normalised: list[str]
    ) -> Optional[FieldValue]:
        """Label and value on one line: ``survey no: 142/B``."""
        pattern = rule.inline_pattern
        best: Optional[tuple[float, FieldValue]] = None
        for index, text in enumerate(normalised):
            match = pattern.search(text)
            if not match or not match.group("value").strip():
                continue
            score = INLINE_WITH_SEPARATOR if match.group("sep") else INLINE_WITHOUT_SEPARATOR
            field = self._build(
                rule,
                lines[index],
                rule.normalise_value(match.group("value")),
                score,
            )
            if best is None or score > best[0]:
                best = (score, field)
        return best[1] if best else None

    def _match_adjacent(
        self, rule: FieldRule, lines: list[OcrLine], normalised: list[str]
    ) -> Optional[FieldValue]:
        """Two-column layouts where the label and value are on separate lines."""
        label_pattern = rule.label_pattern
        value_pattern = rule.value_pattern
        for index, text in enumerate(normalised[:-1]):
            if not label_pattern.match(text.strip(" :#-–")):
                continue
            label_line, value_line = lines[index], lines[index + 1]
            next_text = normalised[index + 1]
            if value_line.page != label_line.page or not value_pattern.match(next_text):
                continue
            return self._build(
                rule,
                value_line,
                rule.normalise_value(next_text),
                ADJACENT_LINE,
                original_text=f"{label_line.text} {value_line.text}".strip(),
                warning="value_from_adjacent_line",
            )
        return None

    def _match_unit_suffix(
        self, rule: FieldRule, lines: list[OcrLine], normalised: list[str]
    ) -> Optional[FieldValue]:
        """Number followed by its unit where no label precedes it: ``2.5 ఎకరాలు``."""
        pattern = rule.unit_value_pattern
        if pattern is None:
            return None
        for index, text in enumerate(normalised):
            match = pattern.search(text)
            if not match or not match.group("value").strip():
                continue
            value = rule.normalise_value(match.group("value"))
            unit = match.group("unit")
            return self._build(
                rule,
                lines[index],
                f"{value} {unit}".strip(),
                UNIT_SUFFIX,
                warning="value_anchored_on_unit_not_label",
            )
        return None


def classify_document_type_by_keywords(
    text: str, config: StateConfig
) -> tuple[Optional[str], Optional[float]]:
    """Provisional document-type classification from title keywords.

    Returns ``(type, score)`` or ``(None, None)`` when no keyword matched. This
    is a fallback used until the EfficientNet document classifier is trained; the
    pipeline records which method produced the type.
    """
    lowered = text.lower()
    best: Optional[tuple[str, float]] = None
    for name, spec in config.document_types.items():
        keywords = [k.lower() for k in spec.get("title_keywords_en", [])]
        keywords += [k for k in spec.get("title_keywords_te", [])]
        for keyword in keywords:
            if keyword and keyword in lowered:
                score = min(0.8, 0.4 + 0.1 * len(keyword.split()))
                if best is None or score > best[1]:
                    best = (name, score)
    return best if best else (None, None)
