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

_IMPRINT_PATH = Path(__file__).resolve().parents[2] / "backend" / "seed" / "data" / "imprint.md"


@pytest.mark.asyncio
async def test_imprint_route() -> None:
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/imprint").raise_for_status()
    imprint: Final = ImprintResponseV1.model_validate(response.json())

    assert response.status_code == 200
    assert imprint.content == _IMPRINT_PATH.read_text(encoding="utf-8")
