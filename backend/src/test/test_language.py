from typing import Final
from typing import Optional

import pytest
from fastapi import HTTPException
from fastapi import Response

from backend.routes.v1.language import get_display_language


@pytest.mark.asyncio
async def test_display_language_selects_supported_language() -> None:
    response: Final = Response()

    result: Final = await get_display_language(
        response,
        language="de-AT",
        supported_language=["de", "en"],
        accept_language="en",
    )

    assert result.available_languages == ["de", "en"]
    assert result.language_tag == "de"
    assert result.is_language_fallback is False
    assert "vary" not in response.headers


@pytest.mark.asyncio
async def test_display_language_lists_repeated_supported_languages_once() -> None:
    result: Final = await get_display_language(
        Response(),
        supported_language=["de", "en", "de"],
    )

    assert result.available_languages == ["de", "en"]


@pytest.mark.asyncio
async def test_display_language_returns_tags_in_the_spelling_of_the_supported_languages() -> None:
    result: Final = await get_display_language(
        Response(),
        language="he",
        # `en-us` and `iw` are normalized to `en-US` and `he`, `en-US` is another spelling of `en-us`.
        supported_language=["en-us", "iw", "en-US"],
    )

    assert result.available_languages == ["en-us", "iw"]
    assert result.language_tag == "iw"
    assert result.is_language_fallback is False


@pytest.mark.asyncio
async def test_display_language_without_any_preference_returns_english_without_fallback() -> None:
    response: Final = Response()

    result: Final = await get_display_language(response, supported_language=["de", "en"])

    assert result.language_tag == "en"
    assert result.is_language_fallback is False
    assert response.headers["vary"] == "Accept-Language"


@pytest.mark.asyncio
@pytest.mark.parametrize("supported_language", [None, []])
async def test_display_language_returns_bad_request_without_supported_languages(
    supported_language: Optional[list[str]],
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _ = await get_display_language(Response(), supported_language=supported_language)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "At least one supported language must be given."
