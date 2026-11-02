import asyncio
from datetime import timedelta
from functools import partial
from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import httpx2
import pytest

import backend.health as health_module
from backend.health import _OIDC_DISCOVERY_URL  # type: ignore[reportPrivateUsage]
from backend.health import _check_database  # type: ignore[reportPrivateUsage]
from backend.health import _check_identity_provider  # type: ignore[reportPrivateUsage]
from backend.health import _status_of  # type: ignore[reportPrivateUsage]
from backend.health import check_dependencies
from backend.logging.events_gen import DependencyCheckFailed
from backend.models.dependency_status import DependencyStatus
from backend.models.responses import DependencyStatusesV1


def _mock_identity_provider(monkeypatch: pytest.MonkeyPatch, status_code: int) -> list[httpx2.Request]:
    requests: Final[list[httpx2.Request]] = []

    def handle(request: httpx2.Request) -> httpx2.Response:
        requests.append(request)
        return httpx2.Response(status_code)

    monkeypatch.setattr(
        health_module.httpx2,
        "AsyncClient",
        partial(httpx2.AsyncClient, transport=httpx2.MockTransport(handle)),
    )
    return requests


@pytest.mark.asyncio
async def test_check_database_queries_the_database(monkeypatch: pytest.MonkeyPatch) -> None:
    session: Final = AsyncMock()
    context_manager: Final = AsyncMock()
    context_manager.__aenter__.return_value = session
    monkeypatch.setattr(health_module, "ASYNC_SESSION_FACTORY", Mock(return_value=context_manager))

    await _check_database()

    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_check_identity_provider_requests_the_oidc_discovery_document(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: Final = _mock_identity_provider(monkeypatch, 200)

    await _check_identity_provider()

    assert [str(request.url) for request in requests] == [_OIDC_DISCOVERY_URL]


@pytest.mark.asyncio
async def test_check_identity_provider_raises_on_error_status(monkeypatch: pytest.MonkeyPatch) -> None:
    _ = _mock_identity_provider(monkeypatch, 503)

    with pytest.raises(httpx2.HTTPStatusError):
        await _check_identity_provider()


@pytest.mark.asyncio
async def test_status_of_returns_up_when_the_check_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    log_warning: Final = Mock()
    monkeypatch.setattr(health_module.logging, "warning", log_warning)

    assert await _status_of("database", AsyncMock()) == DependencyStatus.UP
    log_warning.assert_not_called()


@pytest.mark.asyncio
async def test_status_of_returns_down_and_logs_when_the_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    log_warning: Final = Mock()
    monkeypatch.setattr(health_module.logging, "warning", log_warning)

    assert (
        await _status_of("database", AsyncMock(side_effect=ConnectionRefusedError("secret host")))
        == DependencyStatus.DOWN
    )
    log_warning.assert_called_once_with(
        DependencyCheckFailed(dependency="database", exception_type="builtins.ConnectionRefusedError"),
    )


@pytest.mark.asyncio
async def test_status_of_returns_down_when_the_check_times_out(monkeypatch: pytest.MonkeyPatch) -> None:
    log_warning: Final = Mock()
    monkeypatch.setattr(health_module.logging, "warning", log_warning)
    monkeypatch.setattr(health_module, "_CHECK_TIMEOUT", timedelta(milliseconds=10))

    async def hang() -> None:
        await asyncio.sleep(10)

    assert await _status_of("identity_provider", hang) == DependencyStatus.DOWN
    log_warning.assert_called_once_with(
        DependencyCheckFailed(dependency="identity_provider", exception_type="builtins.TimeoutError"),
    )


@pytest.mark.asyncio
async def test_check_dependencies_reports_each_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(health_module, "_check_database", AsyncMock())
    monkeypatch.setattr(health_module, "_check_identity_provider", AsyncMock(side_effect=OSError()))
    monkeypatch.setattr(health_module.logging, "warning", Mock())

    assert await check_dependencies() == DependencyStatusesV1(
        database=DependencyStatus.UP, identity_provider=DependencyStatus.DOWN
    )
