"""Structured logging façade for the backend.

Usage::

    from backend import logging

    logging.info(HttpRequestReceived(method="GET", path="/v1/globals"))

All log records are emitted as JSON-lines to `stdout`. When the `LOG_FILE`
environment variable is set the same records are additionally appended to that
file.

The serialized format is intentionally aligned with the OpenTelemetry Logs Data
Model so that future trace/span correlation requires no schema changes.
"""

import os
import sys
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import IO
from typing import Final
from typing import Optional
from typing import final

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field
from pydantic import field_serializer

from backend.logging.events_gen import LogEvent

# ---------------------------------------------------------------------------
# File sink configuration (read once at import time)
# ---------------------------------------------------------------------------


def _try_open_log_file(path: Optional[Path]) -> Optional[IO[str]]:
    if path is None:
        return None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        return path.open(
            "a",
            encoding="utf-8",
        )
    except Exception as e:
        print(
            f"error: failed to open log file '{path}': {e}",
            file=sys.stderr,
        )
        return None


_LOG_FILE = (
    _try_open_log_file(Path(log_file_path_string))
    if (log_file_path_string := os.environ.get("LOG_FILE")) is not None
    else None
)


@final
class _SeverityText(StrEnum):
    """
    Severity text values aligned with OpenTelemetry Logs Data Model (and therefore uppercase).
    """

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@final
class _LogRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    timestamp: datetime
    severity_text: _SeverityText
    body: str
    attributes: LogEvent
    trace_id: Optional[str]
    span_id: Optional[str]

    @field_serializer("attributes")
    def _serialize_attributes(self, value: LogEvent) -> dict[str, object]:
        # This is a filed serializer because we want to keep `trace_id` and
        # `span_id` at the top level of the log record, even when they’re `None`.
        # For the nested elements, however, we want to omit `None` values.
        return value.model_dump(exclude_none=True)

    @computed_field(alias="event.name")
    @property
    def event_name(self) -> str:
        return self.attributes.LOG_EVENT_NAME


def _build_record(event: LogEvent, severity_text: _SeverityText) -> _LogRecord:
    return _LogRecord(
        timestamp=datetime.now(UTC),
        severity_text=severity_text,
        body=event.LOG_BODY,
        attributes=event,
        trace_id=None,
        span_id=None,
    )


def _emit(event: LogEvent, severity_text: _SeverityText) -> None:
    contents: Final = _build_record(event, severity_text).model_dump_json(by_alias=True)
    line: Final = f"{contents}\n"
    print(line, end="", file=sys.stdout, flush=True)
    if _LOG_FILE is not None:
        print(line, end="", file=_LOG_FILE, flush=True)


def debug(event: LogEvent) -> None:
    """Emit a DEBUG-severity log record."""
    _emit(event, _SeverityText.DEBUG)


def info(event: LogEvent) -> None:
    """Emit an INFO-severity log record."""
    _emit(event, _SeverityText.INFO)


def warning(event: LogEvent) -> None:
    """Emit a WARNING-severity log record."""
    _emit(event, _SeverityText.WARNING)


def error(event: LogEvent) -> None:
    """Emit an ERROR-severity log record."""
    _emit(event, _SeverityText.ERROR)


def critical(event: LogEvent) -> None:
    """Emit a CRITICAL-severity log record."""
    _emit(event, _SeverityText.CRITICAL)
