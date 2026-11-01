from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi import Response

from backend.models.responses import GlobalsResponseV1
from backend.models.tables import GlobalKey
from backend.models.tables import GlobalTranslation
from backend.routes.v1.globals import get_globals


def _footer_text(language_tag: str) -> GlobalTranslation:
    return GlobalTranslation(
        key=GlobalKey.FOOTER_TEXT,
        language_tag=language_tag,
        value=f"Footer ({language_tag})",
    )


def _session_with_translations(translations: list[GlobalTranslation]) -> AsyncMock:
    session: Final = AsyncMock()
    session.execute.return_value = Mock(scalars=Mock(return_value=translations))
    return session


@pytest.mark.asyncio
async def test_globals_returns_requested_language() -> None:
    response: Final = Response()
    session: Final = _session_with_translations([_footer_text("de"), _footer_text("en")])

    result: Final = await get_globals(["de"], response, session)

    assert isinstance(result, GlobalsResponseV1)
    assert result.footer_text == "Footer (de)"
    assert result.language_details.available_languages == ["de", "en"]
    assert result.language_details.language_tag == "de"
    assert result.language_details.is_language_fallback is False
    assert response.headers["Content-Language"] == "de"
    session.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_globals_matches_regional_requests_case_insensitively() -> None:
    response: Final = Response()
    session: Final = _session_with_translations([_footer_text("de"), _footer_text("en")])

    result: Final = await get_globals(["DE-at"], response, session)

    assert result.footer_text == "Footer (de)"
    assert result.language_details.language_tag == "de"
    assert result.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_globals_falls_back_to_english_when_requested_language_is_missing() -> None:
    response: Final = Response()
    session: Final = _session_with_translations([_footer_text("de"), _footer_text("en"), _footer_text("es")])

    result: Final = await get_globals(["fr"], response, session)

    assert result.footer_text == "Footer (en)"
    assert result.language_details.available_languages == ["de", "en", "es"]
    assert result.language_details.language_tag == "en"
    assert result.language_details.is_language_fallback is True
    assert response.headers["Content-Language"] == "en"


@pytest.mark.asyncio
async def test_globals_falls_back_to_first_language_when_english_is_missing() -> None:
    response: Final = Response()
    session: Final = _session_with_translations([_footer_text("es"), _footer_text("de")])

    result: Final = await get_globals(["fr"], response, session)

    assert result.footer_text == "Footer (de)"
    assert result.language_details.available_languages == ["de", "es"]
    assert result.language_details.language_tag == "de"
    assert result.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_globals_raises_exception_when_not_found() -> None:
    response: Final = Response()
    session: Final = _session_with_translations([])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_globals(["de"], response, session)
    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Global values not found in the database."
