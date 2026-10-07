from pathlib import Path
from typing import Final

import httpx
import pytest
from langcodes import Language

from backend.config import SETTINGS
from backend.models.responses import ImprintResponseV1

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]

_DATA_PATH = Path(__file__).resolve().parents[2] / "backend" / "seed" / "data"
_IMPRINT_URL = f"{SETTINGS.backend_root_uri}/v1/imprint"


def _imprint_content(language_tag: str) -> str:
    return (_DATA_PATH / f"imprint.{language_tag}.md").read_text(encoding="utf-8")


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["de", "en"])
async def test_imprint_route_returns_requested_language(language_tag: str) -> None:
    response: Final = httpx.get(_IMPRINT_URL, params={"language": language_tag}).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert response.status_code == 200
    assert imprint.content == _imprint_content(language_tag)
    assert imprint.language_details.available_languages == [Language.get("de"), Language.get("en")]
    assert imprint.language_details.language_tag == Language.get(language_tag)
    assert imprint.language_details.is_language_fallback is False
    # The selection did not depend on `Accept-Language`, so caches may share the response.
    assert "accept-language" not in response.headers.get("vary", "").lower()


@pytest.mark.asyncio
async def test_imprint_route_falls_back_to_english() -> None:
    response: Final = httpx.get(_IMPRINT_URL, params={"language": "es"}).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == _imprint_content("en")
    assert imprint.language_details.available_languages == [Language.get("de"), Language.get("en")]
    assert imprint.language_details.language_tag == Language.get("en")
    assert imprint.language_details.is_language_fallback is True


@pytest.mark.asyncio
async def test_imprint_route_without_any_preference_returns_english() -> None:
    response: Final = httpx.get(_IMPRINT_URL).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == _imprint_content("en")
    assert imprint.language_details.language_tag == Language.get("en")
    # The client did not ask for any language, so English is not a fallback.
    assert imprint.language_details.is_language_fallback is False
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
async def test_imprint_route_without_language_uses_accept_language_header() -> None:
    response: Final = httpx.get(_IMPRINT_URL, headers={"Accept-Language": "fr;q=0.9, de-AT;q=0.8"}).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == _imprint_content("de")
    assert imprint.language_details.language_tag == Language.get("de")
    # French was preferred, so German is a fallback.
    assert imprint.language_details.is_language_fallback is True
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
async def test_imprint_route_ignores_invalid_accept_language_header() -> None:
    response: Final = httpx.get(_IMPRINT_URL, headers={"Accept-Language": "!!!"}).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == _imprint_content("en")
    assert imprint.language_details.language_tag == Language.get("en")
    assert imprint.language_details.is_language_fallback is False
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
async def test_imprint_route_handles_invalid_language_like_an_unavailable_one() -> None:
    response: Final = httpx.get(_IMPRINT_URL, params={"language": "en_US"}).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == _imprint_content("en")
    assert imprint.language_details.language_tag == Language.get("en")
    assert imprint.language_details.is_language_fallback is True
