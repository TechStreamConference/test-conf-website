import json
import re
from collections.abc import AsyncGenerator
from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import Request
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

import backend.main as main_module
from backend.database import get_session
from backend.logging.events_gen import ApplicationStarted
from backend.logging.events_gen import ApplicationStopping
from backend.logging.events_gen import HttpRequestCompleted
from backend.logging.events_gen import HttpRequestFailed
from backend.logging.events_gen import HttpRequestReceived
from backend.main import _lifespan  # type: ignore[reportPrivateUsage]
from backend.main import _log_requests  # type: ignore[reportPrivateUsage]
from backend.main import app
from backend.main import database_health


@pytest.mark.asyncio
async def test_database_health_returns_ok() -> None:
    session: Final = AsyncMock()

    result: Final = await database_health(session)

    assert result == {"ok": True}
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_lifespan_logs_startup_and_shutdown(monkeypatch: pytest.MonkeyPatch) -> None:
    log_info: Final = Mock()
    monkeypatch.setattr(main_module.logging, "info", log_info)

    async with _lifespan(app):
        assert log_info.call_count == 1
        started: Final = log_info.call_args.args[0]
        assert isinstance(started, ApplicationStarted)
        assert started.host == main_module.SETTINGS.server_host
        assert started.port == main_module.SETTINGS.server_port

    assert log_info.call_count == 2
    assert isinstance(log_info.call_args.args[0], ApplicationStopping)


@pytest.mark.asyncio
async def test_request_middleware_logs_received_and_completed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request: Final = Mock()
    request.method = "GET"
    request.url.path = "/health/database"
    expected_response: Final = Response(status_code=204)
    call_next: Final = AsyncMock(return_value=expected_response)
    log_info: Final = Mock()
    monotonic: Final = Mock(side_effect=[10.0, 10.01234])
    monkeypatch.setattr(main_module.logging, "info", log_info)
    monkeypatch.setattr(main_module, "time", Mock(monotonic=monotonic))

    result: Final = await _log_requests(request, call_next)

    assert result is expected_response
    call_next.assert_awaited_once_with(request)
    assert log_info.call_count == 2
    received: Final = log_info.call_args_list[0].args[0]
    completed: Final = log_info.call_args_list[1].args[0]
    assert isinstance(received, HttpRequestReceived)
    assert received.method == "GET"
    assert received.path == "/health/database"
    assert isinstance(completed, HttpRequestCompleted)
    assert completed.method == "GET"
    assert completed.path == "/health/database"
    assert completed.status_code == 204
    assert completed.duration_ms == 12.34


@pytest.mark.asyncio
async def test_request_middleware_returns_unexpected_exceptions_as_internal_server_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    request: Final = Mock()
    request.method = "GET"
    request.url.path = "/v1/imprint"
    log_info: Final = Mock()
    log_error: Final = Mock()
    monkeypatch.setattr(main_module.logging, "info", log_info)
    monkeypatch.setattr(main_module.logging, "error", log_error)
    monkeypatch.setattr(main_module, "time", Mock(monotonic=Mock(side_effect=[10.0, 10.5])))

    async def _call_next(_request: Request) -> Response:
        raise RuntimeError("Key (email)=(jane@example.com) already exists.")

    response: Final = await _log_requests(request, _call_next)

    assert response.status_code == 500
    assert json.loads(bytes(response.body)) == {"detail": "Internal server error."}
    log_error.assert_called_once()
    failed: Final = log_error.call_args.args[0]
    assert isinstance(failed, HttpRequestFailed)
    assert failed.method == "GET"
    assert failed.path == "/v1/imprint"
    assert failed.exception_type == "builtins.RuntimeError"
    # Only code locations, never the message, which may contain personal data.
    locations: Final = failed.exception_stack.splitlines()
    assert len(locations) == 2
    assert re.fullmatch(r"backend\.main:\d+ in _log_requests", locations[0])
    assert re.fullmatch(re.escape(__name__) + r":\d+ in " + re.escape(_call_next.__qualname__), locations[1])
    assert log_info.call_count == 2
    completed: Final = log_info.call_args_list[1].args[0]
    assert isinstance(completed, HttpRequestCompleted)
    assert completed.path == "/v1/imprint"
    assert completed.status_code == 500
    assert completed.duration_ms == 500.0


def test_unexpected_exception_is_returned_as_documented_internal_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def _failing_session() -> AsyncGenerator[AsyncSession]:
        raise RuntimeError("unexpected")
        yield  # pyright: ignore[reportUnreachable]

    log_info: Final = Mock()
    monkeypatch.setattr(main_module.logging, "info", log_info)
    app.dependency_overrides[get_session] = _failing_session
    try:
        # Raises if the exception reaches the server, which would log it with its message as an unstructured traceback.
        response: Final = TestClient(app).get("/v1/globals")
    finally:
        _ = app.dependency_overrides.pop(get_session)

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error."}
    completed: Final = [
        call.args[0] for call in log_info.call_args_list if isinstance(call.args[0], HttpRequestCompleted)
    ]
    assert [event.status_code for event in completed] == [500]


def test_request_middleware_logs_the_path_without_the_query_string(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _failing_session() -> AsyncGenerator[AsyncSession]:
        raise RuntimeError("unexpected")
        yield  # pyright: ignore[reportUnreachable]

    log_info: Final = Mock()
    log_error: Final = Mock()
    monkeypatch.setattr(main_module.logging, "info", log_info)
    monkeypatch.setattr(main_module.logging, "error", log_error)
    app.dependency_overrides[get_session] = _failing_session
    try:
        # Query strings may contain personal data.
        _ = TestClient(app).get("/v1/globals", params={"language": "de"})
    finally:
        _ = app.dependency_overrides.pop(get_session)

    logged: Final = [call.args[0] for call in log_info.call_args_list + log_error.call_args_list]
    assert [type(event) for event in logged] == [HttpRequestReceived, HttpRequestCompleted, HttpRequestFailed]
    assert all(event.path == "/v1/globals" for event in logged)
