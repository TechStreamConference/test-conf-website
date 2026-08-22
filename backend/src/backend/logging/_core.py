import json
import os
import sys
from datetime import UTC
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import IO
from typing import Final
from typing import Optional
from typing import cast
from typing import final

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import computed_field
from pydantic import field_serializer

from backend.config import SETTINGS
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
        # This is a field serializer because we want to keep `trace_id` and
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


# ---------------------------------------------------------------------------
# Dev pretty-printing (stdout only; never touches the file sink)
# ---------------------------------------------------------------------------

_SERVICE_NAME = "backend"

_R = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_BLUE = "\033[34m"
_MAGENTA = "\033[35m"
_CYAN = "\033[36m"
_BOLD_RED = "\033[1;31m"

_SEVERITY_COLORS = {
    "DEBUG": _DIM,
    "INFO": _GREEN,
    "WARNING": _YELLOW,
    "ERROR": _RED,
    "CRITICAL": _BOLD_RED,
}


def _colorize_json(value: object, indent: int = 0) -> str:
    pad: Final = "  " * indent
    inner: Final = "  " * (indent + 1)
    # `bool` must be checked before `int` since `bool` subclasses `int`.
    match value:
        case bool():
            return f"{_MAGENTA}{'true' if value else 'false'}{_R}"
        case int() | float():
            return f"{_YELLOW}{value}{_R}"
        case str():
            escaped: Final = value.replace("\\", "\\\\").replace('"', '\\"')
            return f'{_GREEN}"{escaped}"{_R}'
        case None:
            return f"{_DIM}null{_R}"
        case dict():
            if not value:
                return "{}"
            lines = [
                f'{inner}{_BOLD}{_CYAN}"{k}"{_R}: {_colorize_json(v, indent + 1)}'
                for k, v in cast(dict[str, object], value).items()
            ]
            return "{\n" + ",\n".join(lines) + "\n" + pad + "}"
        case list():
            if not value:
                return "[]"
            lines = [f"{inner}{_colorize_json(v, indent + 1)}" for v in cast(list[object], value)]
            return "[\n" + ",\n".join(lines) + "\n" + pad + "]"
        case _:
            return repr(value)


def _format_pretty(record: _LogRecord) -> str:
    sev_color: Final = _SEVERITY_COLORS.get(str(record.severity_text), "")
    sev_text: Final = f"{record.severity_text:<8}"
    header: Final = (
        f"{_BOLD}{_BLUE}[{_SERVICE_NAME}]{_R} {sev_color}{_BOLD}{sev_text}{_R} {_BOLD}{record.event_name}{_R}"
    )
    data: Final = json.loads(record.model_dump_json(by_alias=True))
    return header + "\n" + _colorize_json(data)


def _emit(event: LogEvent, severity_text: _SeverityText) -> None:
    record: Final = _build_record(event, severity_text)
    line: Final = record.model_dump_json(by_alias=True) + "\n"
    if SETTINGS.environment == "dev":
        print(_format_pretty(record), file=sys.stdout, flush=True)
    else:
        print(line, end="", file=sys.stdout, flush=True)
    if _LOG_FILE is not None:
        print(line, end="", file=_LOG_FILE, flush=True)


def debug(event: LogEvent) -> None:
    _emit(event, _SeverityText.DEBUG)


def info(event: LogEvent) -> None:
    _emit(event, _SeverityText.INFO)


def warning(event: LogEvent) -> None:
    _emit(event, _SeverityText.WARNING)


def error(event: LogEvent) -> None:
    _emit(event, _SeverityText.ERROR)


def critical(event: LogEvent) -> None:
    _emit(event, _SeverityText.CRITICAL)
