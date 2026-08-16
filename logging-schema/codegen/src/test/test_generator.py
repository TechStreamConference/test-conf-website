"""Tests for the code generator (template rendering)."""

import json
import tempfile
from pathlib import Path

import pytest

from codegen.generator import generate_python
from codegen.generator import generate_typescript
from codegen.models import EventModel
from codegen.parser import parse_schema_dir

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_MINIMAL_SCHEMA: dict[str, object] = {
    "$id": "SampleEvent.json",
    "type": "object",
    "x-event-name": "sample.event",
    "x-event-body": "Sample event",
    "properties": {
        "name": {"type": "string"},
        "count": {"type": "integer"},
        "tag": {"type": "string"},
    },
    "required": ["name", "count"],
}

_EMPTY_SCHEMA: dict[str, object] = {
    "$id": "EmptyEvent.json",
    "type": "object",
    "x-event-name": "empty.event",
    "x-event-body": "Empty event",
}


def _schema_dir_with(*schemas: dict[str, object]) -> Path:
    """Create a temp dir, write schemas, return its path (caller owns cleanup)."""
    tmp = tempfile.mkdtemp()
    d = Path(tmp)
    for s in schemas:
        name = str(s["$id"])
        _ = (d / name).write_text(json.dumps(s), encoding="utf-8")
    return d


def _models() -> list[EventModel]:
    d = _schema_dir_with(_MINIMAL_SCHEMA, _EMPTY_SCHEMA)
    return parse_schema_dir(d)


# ---------------------------------------------------------------------------
# Python generator
# ---------------------------------------------------------------------------


def test_generate_python_creates_file() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    assert output.exists()
    assert output.stat().st_size > 0


def test_generate_python_header_comment() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "Do not edit manually" in content
    assert "just gen-log-models" in content


def test_generate_python_class_names() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "class SampleEvent(LogEventBase):" in content
    assert "class EmptyEvent(LogEventBase):" in content


def test_generate_python_event_metadata() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert 'LOG_EVENT_NAME: ClassVar[str] = "sample.event"' in content
    assert 'LOG_BODY: ClassVar[str] = "Sample event"' in content


def test_generate_python_required_field() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "name: str" in content
    assert "count: int" in content


def test_generate_python_optional_field() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "tag: str | None = None" in content


def test_generate_python_imports() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "from typing import ClassVar" in content
    assert "from backend.logging._base import LogEventBase" in content


def test_generate_python_deterministic() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f1:
        out1 = Path(f1.name)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f2:
        out2 = Path(f2.name)
    generate_python(models, out1)
    generate_python(models, out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# TypeScript generator
# ---------------------------------------------------------------------------


def test_generate_typescript_creates_file() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    assert output.exists()
    assert output.stat().st_size > 0


def test_generate_typescript_header_comment() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "Do not edit manually" in content
    assert "just gen-log-models" in content


def test_generate_typescript_zod_import() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "import { z } from 'zod'" in content


def test_generate_typescript_schema_const() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "export const SampleEventSchema = z.object(" in content


def test_generate_typescript_event_metadata() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "eventName: 'sample.event'" in content
    assert "body: 'Sample event'" in content


def test_generate_typescript_constructor_function() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "export function sampleEvent(" in content
    assert "export function emptyEvent(" in content


def test_generate_typescript_optional_field() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "z.string().optional()" in content


def test_generate_typescript_deterministic() -> None:
    models = _models()
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f1:
        out1 = Path(f1.name)
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f2:
        out2 = Path(f2.name)
    generate_typescript(models, out1)
    generate_typescript(models, out2)
    assert out1.read_text(encoding="utf-8") == out2.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# End-to-end: parse real schema → generate → verify round-trip
# ---------------------------------------------------------------------------

_REAL_SCHEMA_DIR = Path(__file__).parent.parent.parent.parent / "schema"


def test_e2e_parse_real_schemas() -> None:
    """Parse the committed JSON Schema files and verify the expected events."""
    if not _REAL_SCHEMA_DIR.is_dir():
        pytest.skip("Schema directory not found (run from logging-schema/codegen)")
    models = parse_schema_dir(_REAL_SCHEMA_DIR)
    event_names = {m.event_name for m in models}
    assert "application.started" in event_names
    assert "application.stopping" in event_names
    assert "http.request.received" in event_names
    assert "http.request.completed" in event_names
    assert "bff.backend_call.completed" in event_names


def test_e2e_generate_python_from_real_schemas() -> None:
    """Generate Python from real schemas and verify key signatures."""
    if not _REAL_SCHEMA_DIR.is_dir():
        pytest.skip("Schema directory not found")
    models = parse_schema_dir(_REAL_SCHEMA_DIR)
    with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
        output = Path(f.name)
    generate_python(models, output)
    content = output.read_text(encoding="utf-8")
    assert "class ApplicationStarted(LogEventBase):" in content
    assert "class ApplicationStopping(LogEventBase):" in content
    assert "host: str" in content
    assert "port: int" in content


def test_e2e_generate_typescript_from_real_schemas() -> None:
    """Generate TypeScript from real schemas and verify key signatures."""
    if not _REAL_SCHEMA_DIR.is_dir():
        pytest.skip("Schema directory not found")
    models = parse_schema_dir(_REAL_SCHEMA_DIR)
    with tempfile.NamedTemporaryFile(suffix=".ts", delete=False) as f:
        output = Path(f.name)
    generate_typescript(models, output)
    content = output.read_text(encoding="utf-8")
    assert "ApplicationStartedSchema" in content
    assert "applicationStarted" in content
