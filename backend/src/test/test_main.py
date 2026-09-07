from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import Response

import backend.main as main_module
from backend.logging.events_gen import ApplicationStarted
from backend.logging.events_gen import ApplicationStopping
from backend.logging.events_gen import HttpRequestCompleted
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
