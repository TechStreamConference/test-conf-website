"""Internal representation for the log-event code generator."""

from dataclasses import dataclass


@dataclass(frozen=True)
class FieldSpec:
    """A single field in a log event model."""

    name: str
    python_type: str  # e.g. "str", "int", "float", "bool", "str | None"
    zod_expr: str  # e.g. "z.string()", "z.number().int().optional()"
    required: bool


@dataclass(frozen=True)
class EventModel:
    """Parsed representation of one TypeSpec log event model."""

    class_name: str  # PascalCase, e.g. "ApplicationStarted"
    fn_name: str  # camelCase constructor, e.g. "applicationStarted"
    event_name: str  # stable identifier, e.g. "application.started"
    event_body: str  # human-readable message, e.g. "Application started"
    fields: tuple[FieldSpec, ...]
