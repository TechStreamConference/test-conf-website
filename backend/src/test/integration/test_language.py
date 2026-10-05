from typing import Final

import httpx
import pytest

from backend.config import SETTINGS
from backend.models.responses import DisplayLanguageResponseV1
from backend.models.responses import MissingSupportedLanguagesResponseV1

pytestmark: Final = pytest.mark.integration

_DISPLAY_LANGUAGE_URL = f"{SETTINGS.backend_root_uri}/v1/display-language"


@pytest.mark.asyncio
async def test_display_language_route_selects_from_repeated_query_parameters() -> None:
    response: Final = httpx.get(
        _DISPLAY_LANGUAGE_URL,
        params=[("supported_language", "de"), ("supported_language", "en"), ("language", "de-CH")],
    ).raise_for_status()
    details: Final = DisplayLanguageResponseV1.model_validate(response.json())

    assert response.json()["availableLanguages"] == ["de", "en"]
    assert details.language_tag == "de"
    assert details.is_language_fallback is False


@pytest.mark.asyncio
async def test_display_language_route_without_any_preference_returns_english_without_fallback() -> None:
    response: Final = httpx.get(
        _DISPLAY_LANGUAGE_URL,
        params=[("supported_language", "de"), ("supported_language", "en")],
    ).raise_for_status()
    details: Final = DisplayLanguageResponseV1.model_validate(response.json())

    assert details.language_tag == "en"
    assert details.is_language_fallback is False
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
async def test_display_language_route_uses_accept_language_header() -> None:
    response: Final = httpx.get(
        _DISPLAY_LANGUAGE_URL,
        params=[("supported_language", "de"), ("supported_language", "en")],
        headers={"Accept-Language": "de-DE"},
    ).raise_for_status()
    details: Final = DisplayLanguageResponseV1.model_validate(response.json())

    assert details.language_tag == "de"
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
async def test_display_language_route_returns_tags_in_the_spelling_of_the_supported_languages() -> None:
    response: Final = httpx.get(
        _DISPLAY_LANGUAGE_URL,
        params=[("supported_language", "en-us"), ("supported_language", "iw")],
        headers={"Accept-Language": "he"},
    ).raise_for_status()

    assert response.json() == {"availableLanguages": ["en-us", "iw"], "languageTag": "iw", "isLanguageFallback": False}


@pytest.mark.asyncio
async def test_display_language_route_rejects_invalid_supported_languages() -> None:
    response: Final = httpx.get(_DISPLAY_LANGUAGE_URL, params=[("supported_language", "en_US")])

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_display_language_route_returns_bad_request_without_supported_languages() -> None:
    response: Final = httpx.get(_DISPLAY_LANGUAGE_URL)

    assert response.status_code == 400
    assert MissingSupportedLanguagesResponseV1.model_validate(response.json()) == MissingSupportedLanguagesResponseV1()
