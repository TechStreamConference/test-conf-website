from pathlib import Path
from typing import Final

import httpx
import pytest

from backend.config import SETTINGS
from backend.models.responses import ImprintResponseV1

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]

_DATA_PATH = Path(__file__).resolve().parents[2] / "backend" / "seed" / "data"


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["de", "en"])
async def test_imprint_route_returns_requested_language(language_tag: str) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/imprint",
        params={"language": language_tag},
    ).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert response.status_code == 200
    assert imprint.content == (_DATA_PATH / f"imprint.{language_tag}.md").read_text(encoding="utf-8")
    assert imprint.language_details.available_languages == ["de", "en"]
    assert imprint.language_details.language_tag == language_tag
    assert imprint.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_imprint_route_falls_back_to_english() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/imprint",
        params={"language": "es"},
    ).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == (_DATA_PATH / "imprint.en.md").read_text(encoding="utf-8")
    assert imprint.language_details.available_languages == ["de", "en"]
    assert imprint.language_details.language_tag == "en"
    assert imprint.language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("headers", "expected_language", "expected_fallback"),
    [
        pytest.param({}, "en", False, id="no preference"),
        pytest.param({"Accept-Language": "fr;q=0.9, de;q=0.8"}, "de", True, id="second preference"),
        pytest.param({"Accept-Language": "de-CH, en;q=0.8"}, "de", False, id="regional preference"),
    ],
)
async def test_imprint_route_negotiates_the_language_from_accept_language(
    headers: dict[str, str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/imprint",
        headers=headers,
    ).raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == (_DATA_PATH / f"imprint.{expected_language}.md").read_text(encoding="utf-8")
    assert imprint.language_details.language_tag == expected_language
    assert imprint.language_details.is_language_fallback is expected_fallback
    assert response.headers["Content-Language"] == expected_language
    assert "Accept-Language" in response.headers["Vary"]


@pytest.mark.asyncio
async def test_imprint_route_prefers_the_language_parameter_over_accept_language() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/imprint",
        params={"language": "de"},
        headers={"Accept-Language": "en"},
    ).raise_for_status()

    assert ImprintResponseV1.model_validate(response.json()).language_details.language_tag == "de"
    assert response.headers["Content-Language"] == "de"
    assert "Accept-Language" not in response.headers.get("Vary", "")
