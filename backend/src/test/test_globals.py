from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from backend.models.tables import Global
from backend.models.tables import GlobalKey
from backend.routes.v1.globals import get_globals


@pytest.mark.asyncio
async def test_get_globals_returns_footer_text() -> None:
    row: Final = Global(key=GlobalKey.FOOTER_TEXT, value="Conference footer")
    result: Final = Mock()
    result.scalars.return_value.all.return_value = [row]
    session: Final = AsyncMock()
    session.execute.return_value = result

    response: Final = await get_globals(session)

    assert response.footer_text == "Conference footer"
    session.execute.assert_awaited_once()
