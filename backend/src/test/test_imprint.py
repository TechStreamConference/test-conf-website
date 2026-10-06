from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi import Response
from langcodes import Language

from backend.language_selection import LanguageRequest
from backend.models.responses import ImprintResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.routes.v1.imprint import get_imprint


def _page(language_tag: str) -> StaticPage:
    return StaticPage(
        kind=StaticPageKind.IMPRINT,
        language=Language.get(language_tag),
        content=f"Imprint ({language_tag})",
    )


def _session_with_pages(pages: list[StaticPage]) -> AsyncMock:
    session: Final = AsyncMock()
    session.execute.return_value = Mock(scalars=Mock(return_value=pages))
    return session


@pytest.mark.asyncio
async def test_imprint_returns_requested_language() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en")])
    response: Final = Response()

    result: Final = await get_imprint(session, LanguageRequest(response, language="de"))

    assert isinstance(result, ImprintResponseV1)
    assert result.content == "Imprint (de)"
    assert result.language_details.available_languages == [Language.get("de"), Language.get("en")]
    assert result.language_details.language_tag == Language.get("de")
    assert result.language_details.is_language_fallback is False
    assert "vary" not in response.headers


@pytest.mark.asyncio
async def test_imprint_matches_route_language_by_canonical_form_and_broader_tag() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en")])

    result: Final = await get_imprint(session, LanguageRequest(Response(), language="DE-at"))

    assert result.language_details.language_tag == Language.get("de")
    assert result.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_imprint_falls_back_to_english_when_requested_language_is_missing() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en"), _page("es")])
    response: Final = Response()

    result: Final = await get_imprint(session, LanguageRequest(response, language="fr"))

    assert result.content == "Imprint (en)"
    assert result.language_details.available_languages == [Language.get("de"), Language.get("en"), Language.get("es")]
    assert result.language_details.language_tag == Language.get("en")
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"


@pytest.mark.asyncio
async def test_imprint_falls_back_to_first_language_when_english_is_missing() -> None:
    session: Final = _session_with_pages([_page("de"), _page("es")])

    result: Final = await get_imprint(session, LanguageRequest(Response(), language="fr"))

    assert result.content == "Imprint (de)"
    assert result.language_details.available_languages == [Language.get("de"), Language.get("es")]
    assert result.language_details.language_tag == Language.get("de")
    assert result.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_imprint_route_language_beats_accept_language_header() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en")])

    result: Final = await get_imprint(session, LanguageRequest(Response(), language="en", accept_language="de"))

    assert result.language_details.language_tag == Language.get("en")
    assert result.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_imprint_uses_header_when_route_language_is_missing() -> None:
    session: Final = _session_with_pages([_page("de"), _page("en")])

    result: Final = await get_imprint(session, LanguageRequest(Response(), language="fr", accept_language="de"))

    assert result.language_details.language_tag == Language.get("de")
    assert result.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_imprint_raises_exception_when_not_found() -> None:
    session: Final = _session_with_pages([])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_imprint(session, LanguageRequest(Response(), language="de"))
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Imprint page not found in the database."
