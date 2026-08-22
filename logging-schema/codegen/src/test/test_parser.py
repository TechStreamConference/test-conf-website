"""Tests for the JSON Schema parser."""

import json
import tempfile
from pathlib import Path

import pytest

from codegen.parser import parse_model
from codegen.parser import parse_schema_dir

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_FULL_SCHEMA: dict[str, object] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "$id": "MyEvent.json",
    "type": "object",
    "x-event-name": "my.event",
    "x-event-body": "My event",
    "properties": {
        "name": {"type": "string", "description": "A name."},
        "count": {"type": "integer", "minimum": -2147483648, "maximum": 2147483647},
        "ratio": {"type": "number"},
        "active": {"type": "boolean"},
        "optional_tag": {"type": "string"},
    },
    "required": ["name", "count", "ratio", "active"],
}


def _write_schema(directory: Path, filename: str, data: dict[str, object]) -> None:
    _ = (directory / filename).write_text(json.dumps(data), encoding="utf-8")


# ---------------------------------------------------------------------------
# _parse_model
# ---------------------------------------------------------------------------


def test_parse_model_basic() -> None:
    model = parse_model(_FULL_SCHEMA, "Fallback")
    assert model.class_name == "MyEvent"
    assert model.fn_name == "myEvent"
    assert model.event_name == "my.event"
    assert model.event_body == "My event"


def test_parse_model_field_count() -> None:
    model = parse_model(_FULL_SCHEMA, "Fallback")
    assert len(model.fields) == 5


def test_parse_model_required_fields() -> None:
    model = parse_model(_FULL_SCHEMA, "Fallback")
    required = {f.name for f in model.fields if f.required}
    optional = {f.name for f in model.fields if not f.required}
    assert required == {"name", "count", "ratio", "active"}
    assert optional == {"optional_tag"}


def test_parse_model_python_types() -> None:
    model = parse_model(_FULL_SCHEMA, "Fallback")
    by_name = {f.name: f for f in model.fields}
    assert by_name["name"].python_type == "str"
    assert by_name["count"].python_type == "int"
    assert by_name["ratio"].python_type == "float"
    assert by_name["active"].python_type == "bool"
    assert by_name["optional_tag"].python_type == "str | None"


def test_parse_model_zod_exprs() -> None:
    model = parse_model(_FULL_SCHEMA, "Fallback")
    by_name = {f.name: f for f in model.fields}
    assert by_name["name"].zod_expr == "z.string()"
    assert by_name["count"].zod_expr == "z.number().int()"
    assert by_name["ratio"].zod_expr == "z.number()"
    assert by_name["active"].zod_expr == "z.boolean()"
    assert by_name["optional_tag"].zod_expr == "z.string().optional()"


def test_parse_model_empty_model() -> None:
    schema: dict[str, object] = {
        "$id": "Empty.json",
        "type": "object",
        "x-event-name": "empty.event",
        "x-event-body": "Empty event",
    }
    model = parse_model(schema, "Fallback")
    assert model.class_name == "Empty"
    assert model.fields == ()


def test_parse_model_fallback_class_name() -> None:
    schema: dict[str, object] = {
        "type": "object",
        "x-event-name": "x.y",
        "x-event-body": "X Y",
    }
    model = parse_model(schema, "FallbackName")
    assert model.class_name == "FallbackName"


def test_parse_model_missing_event_name_raises() -> None:
    schema: dict[str, object] = {
        "$id": "Bad.json",
        "type": "object",
        "x-event-body": "Something",
    }
    with pytest.raises(ValueError, match="x-event-name"):
        _ = parse_model(schema, "Bad")


def test_parse_model_missing_event_body_raises() -> None:
    schema: dict[str, object] = {
        "$id": "Bad.json",
        "type": "object",
        "x-event-name": "some.event",
    }
    with pytest.raises(ValueError, match="x-event-body"):
        _ = parse_model(schema, "Bad")


def test_parse_model_non_object_type_raises() -> None:
    schema: dict[str, object] = {
        "$id": "Bad.json",
        "type": "array",
        "x-event-name": "bad.event",
        "x-event-body": "Bad event",
    }
    with pytest.raises(ValueError, match="unsupported.*type"):
        _ = parse_model(schema, "Bad")


def test_parse_model_unsupported_field_type_raises() -> None:
    schema: dict[str, object] = {
        "$id": "Bad.json",
        "type": "object",
        "x-event-name": "bad.event",
        "x-event-body": "Bad event",
        "properties": {"items": {"type": "array"}},
        "required": ["items"],
    }
    with pytest.raises(ValueError, match="unsupported type"):
        _ = parse_model(schema, "Bad")


# ---------------------------------------------------------------------------
# parse_schema_dir
# ---------------------------------------------------------------------------


def test_parse_schema_dir_lexicographic_order() -> None:
    schema_a: dict[str, object] = {
        "$id": "Alpha.json",
        "type": "object",
        "x-event-name": "alpha.event",
        "x-event-body": "Alpha",
        "properties": {"v": {"type": "string"}},
        "required": ["v"],
    }
    schema_b: dict[str, object] = {
        "$id": "Beta.json",
        "type": "object",
        "x-event-name": "beta.event",
        "x-event-body": "Beta",
    }
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write_schema(d, "Beta.json", schema_b)
        _write_schema(d, "Alpha.json", schema_a)
        models = parse_schema_dir(d)

    assert [m.class_name for m in models] == ["Alpha", "Beta"]


def test_parse_schema_dir_ignores_non_json() -> None:
    schema: dict[str, object] = {
        "$id": "Only.json",
        "type": "object",
        "x-event-name": "only.event",
        "x-event-body": "Only",
    }
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        _write_schema(d, "Only.json", schema)
        _ = (d / "README.md").write_text("ignored", encoding="utf-8")
        models = parse_schema_dir(d)

    assert len(models) == 1
    assert models[0].class_name == "Only"


def test_parse_schema_dir_empty_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        models = parse_schema_dir(Path(tmp))
    assert models == []
