from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.models.responses import ImprintResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.routes.v1.imprint import get_imprint


def _page(language_tag: str) -> StaticPage:
    return StaticPage(
        kind=StaticPageKind.IMPRINT,
        language_tag=language_tag,
        content=f"Imprint ({language_tag})",
    )


def _session_with_pages(pages: list[StaticPage]) -> AsyncMock:
    session: Final = AsyncMock()
    session.execute.return_value = Mock(scalars=Mock(return_value=pages))
    return session


@pytest.mark.asyncio
async def test_imprint_returns_requested_language() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en")])

    result: Final = await get_imprint("de", session)

    assert isinstance(result, ImprintResponseV1)
    assert result.content == "Imprint (de)"
    assert result.language_details.available_languages == ["de", "en"]
    assert result.language_details.language_tag == "de"
    assert result.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_imprint_falls_back_to_english_when_requested_language_is_missing() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en"), _page("es")])

    result: Final = await get_imprint("fr", session)

    assert result.content == "Imprint (en)"
    assert result.language_details.available_languages == ["de", "en", "es"]
    assert result.language_details.language_tag == "en"
    assert result.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_imprint_falls_back_to_first_language_when_english_is_missing() -> None:
    session: Final = _session_with_pages([_page("de"), _page("es")])

    result: Final = await get_imprint("fr", session)

    assert result.content == "Imprint (de)"
    assert result.language_details.available_languages == ["de", "es"]
    assert result.language_details.language_tag == "de"
    assert result.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_imprint_raises_exception_when_not_found() -> None:
    session: Final = _session_with_pages([])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_imprint("de", session)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Imprint page not found in the database."
