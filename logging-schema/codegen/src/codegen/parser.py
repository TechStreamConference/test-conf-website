"""Parse JSON Schema files emitted by TypeSpec into the code generator IR.

Only the subset of JSON Schema produced by the TypeSpec ``@typespec/json-schema``
emitter for our logging schema is supported.  Any unsupported construct raises
a ``ValueError`` with a clear message.
"""

import json
import re
from pathlib import Path
from typing import cast

from codegen.models import EventModel
from codegen.models import FieldSpec


def _to_camel_case(pascal: str) -> str:
    """Convert PascalCase to camelCase."""
    return pascal[0].lower() + pascal[1:] if pascal else pascal


def parse_schema_dir(schema_dir: Path) -> list[EventModel]:
    """Read every ``*.json`` file in *schema_dir* and return the parsed models.

    Files are processed in lexicographic order so that generated output is
    deterministic.
    """
    models: list[EventModel] = []
    for schema_file in sorted(schema_dir.glob("*.json")):
        with schema_file.open(encoding="utf-8") as fh:
            raw = json.load(fh)
        models.append(parse_model(raw, schema_file.stem))
    return models


def parse_model(schema: dict[str, object], default_class_name: str) -> EventModel:
    id_field = schema.get("$id", f"{default_class_name}.json")
    class_name = str(id_field).removesuffix(".json").removesuffix(".yaml")

    event_name = schema.get("x-event-name")
    if not isinstance(event_name, str) or not event_name:
        msg = f"Schema '{class_name}' is missing a non-empty 'x-event-name' extension field."
        raise ValueError(msg)

    event_body = schema.get("x-event-body")
    if not isinstance(event_body, str) or not event_body:
        msg = f"Schema '{class_name}' is missing a non-empty 'x-event-body' extension field."
        raise ValueError(msg)

    schema_type = schema.get("type")
    if schema_type != "object":
        msg = f"Schema '{class_name}' has unsupported top-level type '{schema_type}'. Only 'object' schemas are supported."  # noqa: E501
        raise ValueError(msg)

    required_set: set[str] = set(schema.get("required", []))  # type: ignore[arg-type]
    properties: dict[str, object] = schema.get("properties", {})  # type: ignore[assignment]

    fields = tuple(
        _parse_field(field_name, field_schema, required=field_name in required_set)
        for field_name, field_schema in properties.items()
    )

    return EventModel(
        class_name=class_name,
        fn_name=_to_camel_case(class_name),
        event_name=event_name,
        event_body=event_body,
        fields=fields,
    )


_SUPPORTED_TYPES = frozenset({"string", "integer", "number", "boolean"})

# Map JSON Schema type → (required Python type, optional Python type, Zod expr, optional Zod expr)
_TYPE_MAP: dict[str, tuple[str, str, str, str]] = {
    "string": ("str", "str | None", "z.string()", "z.string().optional()"),
    "integer": ("int", "int | None", "z.number().int()", "z.number().int().optional()"),
    "number": ("float", "float | None", "z.number()", "z.number().optional()"),
    "boolean": ("bool", "bool | None", "z.boolean()", "z.boolean().optional()"),
}

_VALID_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _parse_field(name: str, raw_schema: object, *, required: bool) -> FieldSpec:
    if not _VALID_NAME_RE.match(name):
        msg = f"Field name '{name}' is not a valid Python/TypeScript identifier."
        raise ValueError(msg)

    if not isinstance(raw_schema, dict):
        msg = f"Field '{name}' schema must be a JSON object, got {type(raw_schema).__name__}."
        raise ValueError(msg)

    schema = cast("dict[str, object]", raw_schema)
    field_type = schema.get("type")
    if field_type not in _SUPPORTED_TYPES:
        msg = f"Field '{name}' has unsupported type '{field_type}'. Supported types: {sorted(_SUPPORTED_TYPES)}."
        raise ValueError(msg)

    py_req, py_opt, zod_req, zod_opt = _TYPE_MAP[str(field_type)]
    return FieldSpec(
        name=name,
        python_type=py_req if required else py_opt,
        zod_expr=zod_req if required else zod_opt,
        required=required,
    )
