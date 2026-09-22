"""Generic typed-contract factory backed by an agent definition."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, create_model

from .definition_loader import get_definitions


def build_contracts(definitions=None) -> dict[str, type]:
    definitions = definitions or get_definitions()
    models = definitions["agent-definition.md"].metadata["models"]

    def annotation(field: dict[str, Any]) -> Any:
        field_type = field["type"]
        if field_type == "string":
            return str
        if field_type == "boolean":
            return bool
        if field_type == "integer":
            return int
        if field_type == "string_list":
            return list[str]
        if field_type == "object":
            return dict[str, Any]
        if field_type == "object_list":
            return list[dict[str, Any]]
        if field_type == "float":
            return float
        if field_type == "optional_float":
            return float | None
        if field_type == "optional_int":
            return int | None
        if field_type == "optional_string":
            return str | None
        if field_type == "literal":
            return Literal[tuple(field["values"])]
        raise ValueError(f"Unsupported Markdown contract type: {field_type}")

    result: dict[str, type] = {}
    for name, definition in models.items():
        fields: dict[str, tuple[Any, Any]] = {}
        for field_name, field in definition["fields"].items():
            default = field.get("default")
            if isinstance(default, list):
                default = list(default)
            fields[field_name] = (
                annotation(field),
                Field(default=default, description=field.get("description", "")),
            )
        result[name] = create_model(name, **fields)
    return result


CONTRACTS = build_contracts()
DEFAULTS = get_definitions()["agent-definition.md"].metadata["defaults"]
DEFAULT_LIMIT_VALUE = float(DEFAULTS["limit_value"])
DEFAULT_BASELINE_DEVIATION_PCT = float(DEFAULTS["baseline_deviation_pct"])

TrendFilters = CONTRACTS["TrendFilters"]
DetectionScope = CONTRACTS["DetectionScope"]
FindingsSummary = CONTRACTS["FindingsSummary"]
