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

from backend.logging._core import critical
from backend.logging._core import debug
from backend.logging._core import error
from backend.logging._core import info
from backend.logging._core import warning

__all__ = ["critical", "debug", "error", "info", "warning"]
