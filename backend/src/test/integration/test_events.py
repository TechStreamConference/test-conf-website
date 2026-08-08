from typing import Final

import httpx
import pytest

from backend.config import SETTINGS
from backend.models.responses import EventNotFoundResponseV1
from backend.models.responses import EventResponseV1
from backend.models.responses import InvalidSequenceNumberResponseV1

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]


@pytest.mark.asyncio
async def test_event_route_returns_numbered_and_latest_events() -> None:
    first_response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/en/event/2024/1").raise_for_status()
    second_response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/es/event/2024/2").raise_for_status()
    latest_response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/es/event/2024/latest").raise_for_status()

    first: Final = EventResponseV1.model_validate(first_response.json())
    second: Final = EventResponseV1.model_validate(second_response.json())
    latest: Final = EventResponseV1.model_validate(latest_response.json())

    assert first.id != second.id
    assert first.start_date.year == 2024
    assert first.available_languages == ["de"]
    assert first.language_tag == "de"
    assert first.is_language_fallback is True  # We asked for English, but only German is available.

    assert second.available_languages == ["de", "en", "es"]
    assert second.language_tag == "es"
    assert second.is_language_fallback is False
    assert latest == second


@pytest.mark.asyncio
async def test_event_route_falls_back_to_english() -> None:
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/fr/event/2023/1").raise_for_status()
    event: Final = EventResponseV1.model_validate(response.json())

    assert event.available_languages == ["de", "en"]
    assert event.language_tag == "en"
    assert event.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sequence_number",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
    ],
)
async def test_event_route_rejects_invalid_sequence_numbers(sequence_number: int) -> None:
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/de/event/2024/{sequence_number}")

    assert response.status_code == 400
    assert InvalidSequenceNumberResponseV1.model_validate(response.json()) == InvalidSequenceNumberResponseV1()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("year", "sequence_number"),
    [
        pytest.param(2025, 1, id="year without events"),
        pytest.param(2024, 3, id="nonexistent sequence number"),
    ],
)
async def test_event_route_returns_not_found_for_missing_events(year: int, sequence_number: int) -> None:
    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/de/event/{year}/{sequence_number}")

    assert response.status_code == 404
    assert EventNotFoundResponseV1.model_validate(response.json()) == EventNotFoundResponseV1()
