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
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/{language_tag}/imprint").raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert response.status_code == 200
    assert imprint.content == (_DATA_PATH / f"imprint.{language_tag}.md").read_text(encoding="utf-8")
    assert imprint.available_languages == ["de", "en"]
    assert imprint.language_tag == language_tag
    assert imprint.is_language_fallback is False


@pytest.mark.asyncio
async def test_imprint_route_falls_back_to_english() -> None:
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/es/imprint").raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert imprint.content == (_DATA_PATH / "imprint.en.md").read_text(encoding="utf-8")
    assert imprint.available_languages == ["de", "en"]
    assert imprint.language_tag == "en"
    assert imprint.is_language_fallback is True
