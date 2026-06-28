from typing import Final
from unittest.mock import AsyncMock

import pytest

from backend.main import database_health


@pytest.mark.asyncio
async def test_database_health_returns_ok() -> None:
    session: Final = AsyncMock()

    result: Final = await database_health(session)

    assert result == {"ok": True}
    session.execute.assert_awaited_once()
