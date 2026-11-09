from typing import Final

import httpx
import pytest

from backend.config import SETTINGS
from backend.models.responses import ContentLanguageV1
from backend.models.responses import GlobalsResponseV1

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]

_GERMAN = ContentLanguageV1(language_tag="de", name="Deutsch")
_ENGLISH = ContentLanguageV1(language_tag="en", name="English")

_FOOTER_TEXT_PREFIXES = {
    "de": "TECH STREAM CONFERENCE – Online-Konferenz",
    "en": "TECH STREAM CONFERENCE – Online conference",
}


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["de", "en"])
async def test_globals_route_returns_requested_language(language_tag: str) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/globals",
        params={"language": language_tag},
    ).raise_for_status()
    globals_: Final = GlobalsResponseV1.model_validate(response.json())

    assert response.status_code == 200
    assert globals_.footer_text.startswith(_FOOTER_TEXT_PREFIXES[language_tag])
    assert globals_.language_details.available_languages == [_GERMAN, _ENGLISH]
    assert globals_.language_details.language_tag == language_tag
    assert globals_.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_globals_route_falls_back_to_english() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/globals",
        params={"language": "es"},
    ).raise_for_status()
    globals_: Final = GlobalsResponseV1.model_validate(response.json())

    assert globals_.footer_text.startswith(_FOOTER_TEXT_PREFIXES["en"])
    assert globals_.language_details.available_languages == [_GERMAN, _ENGLISH]
    assert globals_.language_details.language_tag == "en"
    assert globals_.language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("headers", "expected_language", "expected_fallback"),
    [
        pytest.param({}, "en", False, id="no preference"),
        pytest.param({"Accept-Language": "fr;q=0.9, de;q=0.8"}, "de", True, id="second preference"),
        pytest.param({"Accept-Language": "de-CH, en;q=0.8"}, "de", False, id="regional preference"),
    ],
)
async def test_globals_route_negotiates_the_language_from_accept_language(
    headers: dict[str, str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/globals",
        headers=headers,
    ).raise_for_status()
    globals_: Final = GlobalsResponseV1.model_validate(response.json())

    assert globals_.footer_text.startswith(_FOOTER_TEXT_PREFIXES[expected_language])
    assert globals_.language_details.language_tag == expected_language
    assert globals_.language_details.is_language_fallback is expected_fallback
    assert response.headers["Content-Language"] == expected_language
    assert "Accept-Language" in response.headers["Vary"]


@pytest.mark.asyncio
async def test_globals_route_prefers_the_language_parameter_over_accept_language() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/globals",
        params={"language": "de"},
        headers={"Accept-Language": "en"},
    ).raise_for_status()

    assert GlobalsResponseV1.model_validate(response.json()).language_details.language_tag == "de"
    assert response.headers["Content-Language"] == "de"
    assert "Accept-Language" not in response.headers.get("Vary", "")


@pytest.mark.asyncio
async def test_globals_route_rejects_a_malformed_language() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/globals",
        params={"language": "x-foo"},
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Unsupported language tag."}
