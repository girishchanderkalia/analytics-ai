"""Small dependency-free JSON Schema subset used at MCP boundaries."""
from __future__ import annotations
from collections.abc import Mapping
from typing import Any
from .errors import MCPToolSchemaError

def validate_schema_definition(schema: Mapping[str, Any], name: str) -> None:
    if not isinstance(schema, Mapping) or schema.get("type") != "object":
        raise MCPToolSchemaError(f"{name} must be an object JSON Schema")
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    if not isinstance(properties, Mapping) or not isinstance(required, list):
        raise MCPToolSchemaError(f"{name} has invalid properties or required")
    if any(item not in properties for item in required):
        raise MCPToolSchemaError(f"{name} requires an undeclared property")

def validate_instance(value: Mapping[str, Any], schema: Mapping[str, Any], label: str) -> None:
    validate_schema_definition(schema, label + " schema")
    if not isinstance(value, Mapping): raise MCPToolSchemaError(f"{label} must be an object")
    props = schema.get("properties", {})
    for item in schema.get("required", []):
        if item not in value: raise MCPToolSchemaError(f"{label} is missing required field {item!r}")
    for key, item in value.items():
        spec = props.get(key)
        if spec is None:
            if schema.get("additionalProperties", True) is False: raise MCPToolSchemaError(f"{label} contains unknown field {key!r}")
            continue
        expected = spec.get("type") if isinstance(spec, Mapping) else None
        types = {"string": str, "integer": int, "number": (int, float), "boolean": bool, "object": Mapping, "array": list}
        if expected in types and not isinstance(item, types[expected]): raise MCPToolSchemaError(f"{label} field {key!r} must be {expected}")
