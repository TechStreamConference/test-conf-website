from collections.abc import AsyncGenerator
from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Final

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import select

from backend.config import SETTINGS
from backend.models.responses import EventNotFoundResponseV1
from backend.models.responses import EventResponseV1
from backend.models.responses import InvalidSequenceNumberResponseV1
from backend.models.tables import Event

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]


@pytest_asyncio.fixture
async def events_for_current_event_test() -> AsyncGenerator[tuple[AsyncSession, list[Event]]]:
    engine: Final = create_async_engine(
        SETTINGS.async_database_url,
        pool_pre_ping=True,
    )
    session_factory: Final = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    try:
        async with session_factory() as session:
            events: Final = list(
                (await session.execute(select(Event).order_by(col(Event.start_date), col(Event.id)))).scalars()
            )
            assert len(events) >= 3
            original_spotlight_dates: Final = [event.frontpage_spotlight_date for event in events]

            try:
                yield session, events
            finally:
                for event, original_spotlight_date in zip(events, original_spotlight_dates, strict=True):
                    event.frontpage_spotlight_date = original_spotlight_date
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_current_event_route_returns_most_recently_spotlighted_event(
    events_for_current_event_test: tuple[AsyncSession, list[Event]],
) -> None:
    session, events = events_for_current_event_test
    now: Final = datetime.now(UTC).replace(tzinfo=None)
    for event in events:
        event.frontpage_spotlight_date = None
    events[0].frontpage_spotlight_date = now - timedelta(days=2)
    events[1].frontpage_spotlight_date = now - timedelta(days=1)
    events[2].frontpage_spotlight_date = now + timedelta(days=1)
    await session.commit()

    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/en/event").raise_for_status()
    current_event: Final = EventResponseV1.model_validate(response.json())

    assert current_event.id == events[1].id
    assert current_event.language_tag == "en"
    assert current_event.is_language_fallback is False


@pytest.mark.asyncio
async def test_current_event_route_returns_not_found_when_no_event_is_applicable(
    events_for_current_event_test: tuple[AsyncSession, list[Event]],
) -> None:
    session, events = events_for_current_event_test
    future: Final = datetime.now(UTC).replace(tzinfo=None) + timedelta(days=1)
    for index, event in enumerate(events):
        event.frontpage_spotlight_date = None if index % 2 == 0 else future
    await session.commit()

    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/de/event")

    assert response.status_code == 404
    assert EventNotFoundResponseV1.model_validate(response.json()) == EventNotFoundResponseV1()


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
