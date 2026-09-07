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


@pytest.fixture(autouse=True)
def switch_to_staging_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Set the `environment` to “staging” for all tests in this module.

    This is required because in the “dev” environment, logs to `stdout` are pretty-printed
    (thus indented and colorized), which makes naïve JSON parsing of the output fail.
    """
    # We cannot simply change the environment variable because the `SETTINGS` object is instantiated
    # at import time, so we must patch the `environment` attribute directly. For this, we have to
    # patch the object from the module that imports it.
    import backend.logging._core as log_core_module

    mock_settings: Final = log_core_module.SETTINGS.model_copy(update={"environment": "staging"})
    monkeypatch.setattr(log_core_module, "SETTINGS", mock_settings)


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
        import backend.logging._core as logging_core_module

        original_file: Final = logging_core_module._LOG_FILE  # type: ignore[reportPrivateUsage]
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with log_path.open("a", encoding="utf-8") as file_handle:
                # Temporarily patch the module-level file handle.
                logging_core_module._LOG_FILE = file_handle  # type: ignore[reportPrivateUsage]
                captured: Final = StringIO()
                original_stdout: Final = sys.stdout
                sys.stdout = captured  # type: ignore[assignment]
                try:
                    logging_core_module.info(ApplicationStarted(host="filehost", port=3000))
                finally:
                    sys.stdout = original_stdout

            stdout_record: Final = json.loads(captured.getvalue().strip())
            file_record: Final = json.loads(log_path.read_text(encoding="utf-8").strip())
            assert stdout_record == file_record
        finally:
            logging_core_module._LOG_FILE = original_file  # type: ignore[reportPrivateUsage]


def test_dev_environment_pretty_prints_log(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import backend.logging._core as logging_core_module

    settings: Final = logging_core_module.SETTINGS.model_copy(update={"environment": "dev"})
    monkeypatch.setattr(logging_core_module, "SETTINGS", settings)

    logging_core_module.info(ApplicationStarted(host="localhost", port=8080))

    output: Final = capsys.readouterr().out
    assert "[backend]" in output
    assert "INFO" in output
    assert "application.started" in output
    assert '"localhost"' in output
    assert "\033[" in output


@pytest.mark.parametrize(
    ("value", "expected_fragment"),
    [
        (True, "true"),
        (False, "false"),
        (3, "3"),
        (2.5, "2.5"),
        ('quote"and\\slash', 'quote\\"and\\\\slash'),
        (None, "null"),
        ({}, "{}"),
        ([], "[]"),
        ({"nested": [1, None]}, '"nested"'),
        ([{"value": True}], '"value"'),
    ],
)
def test_colorize_json_handles_json_value_types(value: object, expected_fragment: str) -> None:
    import backend.logging._core as logging_core_module

    result: Final = logging_core_module._colorize_json(value)  # type: ignore[reportPrivateUsage]

    assert expected_fragment in result


def test_colorize_json_falls_back_to_repr() -> None:
    import backend.logging._core as logging_core_module

    value: Final = object()

    assert logging_core_module._colorize_json(value) == repr(value)  # type: ignore[reportPrivateUsage]


def test_try_open_log_file_returns_none_without_path() -> None:
    import backend.logging._core as logging_core_module

    assert logging_core_module._try_open_log_file(None) is None  # type: ignore[reportPrivateUsage]


def test_try_open_log_file_creates_parent_and_appends(tmp_path: Path) -> None:
    import backend.logging._core as logging_core_module

    path: Final = tmp_path / "nested" / "backend.jsonl"
    handle: Final = logging_core_module._try_open_log_file(path)  # type: ignore[reportPrivateUsage]
    assert handle is not None
    try:
        _ = handle.write("record\n")
    finally:
        handle.close()

    assert path.read_text(encoding="utf-8") == "record\n"


def test_try_open_log_file_reports_failure(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import backend.logging._core as logging_core_module

    parent_file: Final = tmp_path / "not-a-directory"
    _ = parent_file.write_text("content", encoding="utf-8")

    result: Final = logging_core_module._try_open_log_file(parent_file / "backend.jsonl")  # type: ignore[reportPrivateUsage]

    assert result is None
    assert "failed to open log file" in capsys.readouterr().err


def test_log_file_appends(tmp_path: Path) -> None:
    """Records are appended, not overwritten."""
    log_path: Final = tmp_path / "append.jsonl"
    import backend.logging._core as logging_core_module

    original_file: Final = logging_core_module._LOG_FILE  # type: ignore[reportPrivateUsage]
    try:
        with log_path.open("a", encoding="utf-8") as file_handle:
            logging_core_module._LOG_FILE = file_handle  # type: ignore[reportPrivateUsage]
            devnull: Final = StringIO()
            original_stdout: Final = sys.stdout
            sys.stdout = devnull  # type: ignore[assignment]
            try:
                logging_core_module.info(ApplicationStarted(host="h", port=1))
                logging_core_module.info(ApplicationStopping())
            finally:
                sys.stdout = original_stdout

        lines: Final = log_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 2
    finally:
        logging_core_module._LOG_FILE = original_file  # type: ignore[reportPrivateUsage]
