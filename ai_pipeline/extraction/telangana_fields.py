"""Loads Telangana field/document configuration from ``state_configs``.

Nothing here is Telangana-specific in code: another state becomes available by
adding a directory with the same three JSON files.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional


class ConfigError(RuntimeError):
    pass


def _normalise_digits(value: str) -> str:
    return re.sub(r"\D", "", value)


def _normalise_strip_spaces(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _normalise_collapse_spaces(value: str) -> str:
    return " ".join(value.split())


NORMALISERS = {
    "digits": _normalise_digits,
    "strip_spaces": _normalise_strip_spaces,
    "collapse_spaces": _normalise_collapse_spaces,
}


@dataclass(frozen=True)
class FieldRule:
    name: str
    label_en: str
    label_te: Optional[str]
    ui_label: str
    category: str
    value_type: str
    labels: tuple[str, ...]
    pattern: str
    normalise: str = "collapse_spaces"
    # Optional value-first pattern for layouts whose unit follows the number
    # (e.g. "2.5 ఎకరాలు"), where no label precedes the value. Must expose a
    # named ``value`` group; nothing is extracted when it does not match.
    unit_pattern: Optional[str] = None

    def normalise_value(self, raw: str) -> str:
        func = NORMALISERS.get(self.normalise, _normalise_collapse_spaces)
        return func(raw).strip(" .,:;-")

    @property
    def value_pattern(self) -> re.Pattern[str]:
        return re.compile(f"^(?:{self.pattern})$", re.UNICODE)

    @property
    def label_pattern(self) -> re.Pattern[str]:
        return re.compile(f"^(?:{'|'.join(re.escape(l) for l in self.labels)})$", re.IGNORECASE | re.UNICODE)

    @property
    def unit_value_pattern(self) -> Optional[re.Pattern[str]]:
        if not self.unit_pattern:
            return None
        return re.compile(self.unit_pattern, re.IGNORECASE | re.UNICODE)

    @property
    def inline_pattern(self) -> re.Pattern[str]:
        labels = "|".join(sorted((re.escape(l) for l in self.labels), key=len, reverse=True))
        return re.compile(
            rf"(?P<label>{labels})\s*(?P<sep>[:#\-–]\s*)?(?P<value>{self.pattern})",
            re.IGNORECASE | re.UNICODE,
        )


@dataclass
class StateConfig:
    state: str
    language: str
    fields: dict[str, FieldRule]
    document_types: dict[str, dict]
    validation_rules: dict

    def required_fields(self, document_type: str) -> list[str]:
        table = self.validation_rules.get("required_fields_by_type", {})
        return list(table.get(document_type, []))

    def format_rules(self) -> dict[str, str]:
        return dict(self.validation_rules.get("format_rules", {}))

    def min_ocr_confidence(self) -> float:
        return float(self.validation_rules.get("minimum_ocr_confidence", 0.5))


def _read_json(path: Path) -> dict:
    if not path.exists():
        raise ConfigError(f"Missing state config file: {path}")
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in {path}: {exc}") from exc


@lru_cache(maxsize=4)
def load_state_config(config_dir: Path) -> StateConfig:
    """Load and cache the configuration for one state directory."""
    config_dir = Path(config_dir)
    mapping = _read_json(config_dir / "field_mapping.json")
    document_types = _read_json(config_dir / "document_types.json")
    validation_rules = _read_json(config_dir / "validation_rules.json")

    fields: dict[str, FieldRule] = {}
    for name, spec in mapping.get("fields", {}).items():
        fields[name] = FieldRule(
            name=name,
            label_en=spec.get("label_en", name.replace("_", " ").title()),
            label_te=spec.get("label_te"),
            ui_label=spec.get("ui_label", spec.get("label_en", name)),
            category=spec.get("category", "core"),
            value_type=spec.get("value_type", "text"),
            labels=tuple(spec.get("labels", [])),
            pattern=spec["pattern"],
            normalise=spec.get("normalise", "collapse_spaces"),
            unit_pattern=spec.get("unit_pattern"),
        )

    if not fields:
        raise ConfigError(f"No field definitions found in {config_dir}")

    return StateConfig(
        state=mapping.get("state", document_types.get("state", "unknown")),
        language=mapping.get("language", "te"),
        fields=fields,
        document_types=document_types.get("document_types", {}),
        validation_rules=validation_rules,
    )
