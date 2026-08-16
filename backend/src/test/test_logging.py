"""Tests for the structured logging façade and generated event models."""

import json
import sys
from io import StringIO
from pathlib import Path
from typing import Final
from typing import final

import pytest

from backend.logging._base import LogEventBase
from backend.logging.events_gen import ApplicationStarted
from backend.logging.events_gen import ApplicationStopping
from backend.logging.events_gen import HttpRequestReceived


def _capture_log(event: LogEventBase, level: str = "info") -> dict[str, object]:
    """Call the named logging level with `event` and return the parsed JSONL record."""
    import backend.logging as log_module

    captured: Final = StringIO()
    original: Final = sys.stdout
    try:
        sys.stdout = captured  # type: ignore[assignment]
        # Fetch the appropriate logging function by name from the logging module and
        # call it with the event. During this call, `stdout` is redirected to the
        # `StringIO` buffer so that we can capture the output for inspection.
        getattr(log_module, level)(event)
    finally:
        sys.stdout = original

    line: Final = captured.getvalue().strip()
    return json.loads(line)  # type: ignore[no-any-return]


@final
class TestLogRecordFormat:
    def test_canonical_keys_present(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        assert "timestamp" in record
        assert "severity_text" in record
        assert "body" in record
        assert "event.name" in record
        assert "attributes" in record
        assert "trace_id" in record
        assert "span_id" in record

    def test_severity_text_info(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1), level="info")
        assert record["severity_text"] == "INFO"

    def test_severity_text_debug(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1), level="debug")
        assert record["severity_text"] == "DEBUG"

    def test_severity_text_warning(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1), level="warning")
        assert record["severity_text"] == "WARNING"

    def test_severity_text_error(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1), level="error")
        assert record["severity_text"] == "ERROR"

    def test_severity_text_critical(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1), level="critical")
        assert record["severity_text"] == "CRITICAL"

    def test_body_from_event_metadata(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        assert record["body"] == "Application started"

    def test_event_name_from_event_metadata(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        assert record["event.name"] == "application.started"

    def test_attributes_contain_payload(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="myhost", port=8080))
        attributes: Final = record["attributes"]
        assert isinstance(attributes, dict)
        assert attributes["host"] == "myhost"
        assert attributes["port"] == 8080

    def test_trace_id_is_null(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        assert record["trace_id"] is None

    def test_span_id_is_null(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        assert record["span_id"] is None

    def test_timestamp_is_iso8601_utc(self) -> None:
        record: Final = _capture_log(ApplicationStarted(host="h", port=1))
        ts = str(record["timestamp"])
        # Should end with +00:00 (UTC offset) when using datetime.now(UTC).isoformat()
        assert ts.endswith("+00:00") or ts.endswith("Z")

    def test_output_is_valid_json_line(self) -> None:
        """Each call should produce exactly one JSON object per line."""
        import backend.logging as log_module

        captured: Final = StringIO()
        original: Final = sys.stdout
        try:
            sys.stdout = captured  # type: ignore[assignment]
            log_module.info(ApplicationStarted(host="h", port=1))
            log_module.info(ApplicationStopping())
        finally:
            sys.stdout = original

        lines: Final = captured.getvalue().strip().split("\n")
        assert len(lines) == 2
        for line in lines:
            parsed = json.loads(line)
            assert isinstance(parsed, dict)

    def test_optional_field_omitted_when_none(self) -> None:
        record: Final = _capture_log(HttpRequestReceived(method="GET", path="/"))
        attributes: Final = record["attributes"]
        assert isinstance(attributes, dict)
        assert "request_id" not in attributes


@final
class TestFileLogging:
    def test_log_file_receives_same_record(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """When `LOG_FILE` is set, the same records appear in both `stdout` and the file."""
        log_path: Final = tmp_path / "test.jsonl"
        monkeypatch.setenv("LOG_FILE", str(log_path))

        # Force module reload to pick up the new env var.
        import backend.logging as log_module

        original_file: Final = log_module._LOG_FILE  # type: ignore[reportPrivateUsage]
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as file_handle:
                # Temporarily patch the module-level file handle.
                log_module._LOG_FILE = file_handle  # type: ignore[reportPrivateUsage]
                captured: Final = StringIO()
                original_stdout: Final = sys.stdout
                sys.stdout = captured  # type: ignore[assignment]
                try:
                    log_module.info(ApplicationStarted(host="filehost", port=3000))
                finally:
                    sys.stdout = original_stdout

            stdout_record: Final = json.loads(captured.getvalue().strip())
            file_record: Final = json.loads(log_path.read_text(encoding="utf-8").strip())
            assert stdout_record == file_record
        finally:
            log_module._LOG_FILE = original_file  # type: ignore[reportPrivateUsage]

    def test_log_file_appends(self, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
        """Records are appended, not overwritten."""
        log_path: Final = tmp_path / "append.jsonl"
        import backend.logging as log_module

        original_file: Final = log_module._LOG_FILE  # type: ignore[reportPrivateUsage]
        try:
            with log_path.open("a", encoding="utf-8") as file_handle:
                log_module._LOG_FILE = file_handle  # type: ignore[reportPrivateUsage]
                devnull: Final = StringIO()
                original_stdout: Final = sys.stdout
                sys.stdout = devnull  # type: ignore[assignment]
                try:
                    log_module.info(ApplicationStarted(host="h", port=1))
                    log_module.info(ApplicationStopping())
                finally:
                    sys.stdout = original_stdout

            lines: Final = log_path.read_text(encoding="utf-8").strip().split("\n")
            assert len(lines) == 2
        finally:
            log_module._LOG_FILE = original_file  # type: ignore[reportPrivateUsage]
