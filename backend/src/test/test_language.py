from typing import Final
from typing import Optional

import pytest
from fastapi import HTTPException
from fastapi import Response
from fastapi.testclient import TestClient

from backend.language_selection import LanguageRequest
from backend.main import app
from backend.routes.v1.language import get_display_language


@pytest.mark.asyncio
async def test_display_language_selects_supported_language() -> None:
    response: Final = Response()

    result: Final = await get_display_language(
        LanguageRequest(response, language="de-AT", accept_language="en"), supported_language=["de", "en"]
    )

    assert result.available_languages == ["de", "en"]
    assert result.language_tag == "de"
    assert result.is_language_fallback is False
    assert "vary" not in response.headers


@pytest.mark.asyncio
async def test_display_language_lists_repeated_supported_languages_once() -> None:
    result: Final = await get_display_language(LanguageRequest(Response()), supported_language=["de", "en", "de"])

    assert result.available_languages == ["de", "en"]


@pytest.mark.asyncio
async def test_display_language_returns_tags_in_the_spelling_of_the_supported_languages() -> None:
    result: Final = await get_display_language(
        LanguageRequest(Response(), language="he"), supported_language=["en-us", "iw", "en-US"]
    )

    assert result.available_languages == ["en-us", "iw"]
    assert result.language_tag == "iw"
    assert result.is_language_fallback is False


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("accept_language", "expected_tag", "is_language_fallback"),
    [
        (None, "en-US", False),
        ("de", "de-DE", False),
        ("de-AT, de;q=0.9", "de-DE", False),
        ("en", "en-US", False),
        ("fr", "en-US", True),
    ],
)
async def test_display_language_matches_regional_supported_languages(
    accept_language: Optional[str], expected_tag: str, is_language_fallback: bool
) -> None:
    result: Final = await get_display_language(
        LanguageRequest(Response(), accept_language=accept_language), supported_language=["de-DE", "en-US"]
    )

    assert result.language_tag == expected_tag
    assert result.is_language_fallback is is_language_fallback


@pytest.mark.asyncio
async def test_display_language_without_any_preference_returns_english_without_fallback() -> None:
    response: Final = Response()

    result: Final = await get_display_language(LanguageRequest(response), supported_language=["de", "en"])

    assert result.language_tag == "en"
    assert result.is_language_fallback is False
    assert response.headers["vary"] == "Accept-Language"


@pytest.mark.asyncio
@pytest.mark.parametrize("supported_language", [None, []])
async def test_display_language_returns_bad_request_without_supported_languages(
    supported_language: Optional[list[str]],
) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _ = await get_display_language(LanguageRequest(Response()), supported_language=supported_language)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "At least one supported language must be given."


@pytest.mark.parametrize(
    "tag",
    [
        # Normalized to `sr-Latn-x-…`, which exceeds the length limit although the tag itself does not.
        pytest.param("sh-x-" + "-".join(["abcdefgh"] * 6) + "-abcde", id="overlong"),
        # Normalized to `yue-419-Hant`, which langcodes rejects although it accepts the tag itself.
        pytest.param("zh-yue-419-Hant", id="invalid"),
    ],
)
def test_display_language_rejects_supported_languages_whose_normalized_form_is_invalid(tag: str) -> None:
    response: Final = TestClient(app).get("/v1/display-language", params={"supported_language": [tag, "en"]})

    assert response.status_code == 422


def test_display_language_considers_all_accept_language_lines() -> None:
    response: Final = TestClient(app).get(
        "/v1/display-language",
        params={"supported_language": ["de", "en"]},
        headers=[("Accept-Language", "fr"), ("Accept-Language", "de;q=0.9")],
    )

    assert response.status_code == 200
    assert response.json()["languageTag"] == "de"
