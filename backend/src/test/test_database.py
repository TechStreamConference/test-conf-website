from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

import backend.database as database_module
from backend.database import get_session


@pytest.mark.asyncio
async def test_get_session_yields_and_closes_factory_session(monkeypatch: pytest.MonkeyPatch) -> None:
    session: Final = Mock()
    context_manager: Final = AsyncMock()
    context_manager.__aenter__.return_value = session
    factory: Final = Mock(return_value=context_manager)
    monkeypatch.setattr(database_module, "ASYNC_SESSION_FACTORY", factory)
    generator: Final = get_session()

    yielded: Final = await anext(generator)

    assert yielded is session
    with pytest.raises(StopAsyncIteration):
        _ = await anext(generator)
    factory.assert_called_once_with()
    context_manager.__aenter__.assert_awaited_once()
    context_manager.__aexit__.assert_awaited_once()
