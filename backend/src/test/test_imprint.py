from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.models.responses import ImprintResponse
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.routes.v1.imprint import get_imprint


@pytest.mark.asyncio
async def test_imprint_returns_content() -> None:
    session: Final = AsyncMock()
    session.execute.return_value.scalar_one_or_none = Mock(
        return_value=StaticPage(
            kind=StaticPageKind.IMPRINT,
            content="Imprint",
        )
    )

    result: Final = await get_imprint(session)
    assert isinstance(result, ImprintResponse)
    assert result.content == "Imprint"


@pytest.mark.asyncio
async def test_imprint_raises_exception_when_not_found() -> None:
    session: Final = AsyncMock()
    session.execute.return_value.scalar_one_or_none = Mock(return_value=None)

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_imprint(session)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Imprint page not found in the database."
