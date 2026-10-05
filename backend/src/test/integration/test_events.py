from collections.abc import AsyncGenerator
from datetime import UTC
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import Final

import httpx
import pytest
import pytest_asyncio
from langcodes import Language
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
from backend.models.tables import EventTranslation

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


_SAME_DAY_EVENTS_YEAR = 2099


@pytest_asyncio.fixture
async def events_starting_on_the_same_day() -> AsyncGenerator[list[Event]]:
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
            start_date: Final = date(_SAME_DAY_EVENTS_YEAR, 5, 1)
            events: Final = [
                Event(
                    start_date=start_date,
                    end_date=start_date,
                    discord_url=None,
                    twitch_url=None,
                    youtube_channel_url=None,
                    publish_date=None,
                    call_for_papers_start=None,
                    call_for_papers_end=None,
                    frontpage_spotlight_date=None,
                    speakers_visible_from=None,
                    sponsors_visible_from=None,
                    media_partners_visible_from=None,
                    team_members_visible_from=None,
                    schedule_visible_from=None,
                )
                for _ in range(2)
            ]
            session.add_all(events)
            await session.flush()
            translations: Final = [
                EventTranslation(
                    event_id=event.id,
                    language=Language.get(tag),
                    title=f"Event {event.id}",
                    subtitle="",
                    presskit_url=None,
                    trailer_url=None,
                    trailer_poster_url=None,
                    trailer_subtitles_url=None,
                    description_headline="",
                    description="",
                )
                for event in events
                if event.id is not None
                for tag in ["de", "en"]
            ]
            session.add_all(translations)
            await session.commit()

            try:
                yield events
            finally:
                for translation in translations:
                    await session.delete(translation)
                await session.flush()
                for event in events:
                    await session.delete(event)
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_current_event_route_returns_most_recently_spotlighted_event(
    events_for_current_event_test: tuple[AsyncSession, list[Event]],
) -> None:
    session, events = events_for_current_event_test
    now: Final = datetime.now(UTC)
    for event in events:
        event.frontpage_spotlight_date = None
    events[0].frontpage_spotlight_date = now - timedelta(days=2)
    events[1].frontpage_spotlight_date = now - timedelta(days=1)
    events[2].frontpage_spotlight_date = now + timedelta(days=1)
    await session.commit()

    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/event", params={"language": "en"}).raise_for_status()
    current_event: Final = EventResponseV1.model_validate(response.json())

    assert current_event.id == events[1].id
    assert current_event.language_details.language_tag == Language.get("en")
    assert current_event.language_details.is_language_fallback is False


@pytest.mark.asyncio
async def test_current_event_route_returns_not_found_when_no_event_is_applicable(
    events_for_current_event_test: tuple[AsyncSession, list[Event]],
) -> None:
    session, events = events_for_current_event_test
    future: Final = datetime.now(UTC) + timedelta(days=1)
    for index, event in enumerate(events):
        event.frontpage_spotlight_date = None if index % 2 == 0 else future
    await session.commit()

    response: Final = httpx.get(f"{SETTINGS.backend_root_uri}/v1/event", params={"language": "de"})

    assert response.status_code == 404
    assert EventNotFoundResponseV1.model_validate(response.json()) == EventNotFoundResponseV1()


@pytest.mark.asyncio
async def test_event_route_returns_numbered_and_latest_events() -> None:
    first_response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2024/1", params={"language": "en"}
    ).raise_for_status()
    second_response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2024/2", params={"language": "es"}
    ).raise_for_status()
    latest_response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2024/latest", params={"language": "es"}
    ).raise_for_status()

    first: Final = EventResponseV1.model_validate(first_response.json())
    second: Final = EventResponseV1.model_validate(second_response.json())
    latest: Final = EventResponseV1.model_validate(latest_response.json())

    assert first.id != second.id
    assert first.start_date.year == 2024
    assert first.language_details.available_languages == [Language.get("de")]
    assert first.language_details.language_tag == Language.get("de")
    assert first.language_details.is_language_fallback is True  # We asked for English, but only German is available.

    assert second.language_details.available_languages == [Language.get("de"), Language.get("en"), Language.get("es")]
    assert second.language_details.language_tag == Language.get("es")
    assert second.language_details.is_language_fallback is False
    assert latest == second


@pytest.mark.asyncio
async def test_event_route_keeps_events_starting_on_the_same_day_apart(
    events_starting_on_the_same_day: list[Event],
) -> None:
    responses: Final = [
        httpx.get(f"{SETTINGS.backend_root_uri}/v1/event/{_SAME_DAY_EVENTS_YEAR}/{sequence_number}")
        for sequence_number in [1, 2, 3]
    ]

    numbered_events: Final = [
        EventResponseV1.model_validate(response.raise_for_status().json()) for response in responses[:2]
    ]
    assert [event.id for event in numbered_events] == [event.id for event in events_starting_on_the_same_day]
    for event in numbered_events:
        assert event.language_details.available_languages == [Language.get("de"), Language.get("en")]
    assert responses[2].status_code == 404


@pytest.mark.asyncio
async def test_event_route_falls_back_to_english() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2023/1", params={"language": "fr"}
    ).raise_for_status()
    event: Final = EventResponseV1.model_validate(response.json())

    assert event.language_details.available_languages == [Language.get("de"), Language.get("en")]
    assert event.language_details.language_tag == Language.get("en")
    assert event.language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "sequence_number",
    [
        pytest.param(0, id="zero"),
        pytest.param(-1, id="negative"),
    ],
)
async def test_event_route_rejects_invalid_sequence_numbers(sequence_number: int) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2024/{sequence_number}", params={"language": "de"}
    )

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
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/{year}/{sequence_number}", params={"language": "de"}
    )

    assert response.status_code == 404
    assert EventNotFoundResponseV1.model_validate(response.json()) == EventNotFoundResponseV1()


@pytest.mark.asyncio
async def test_event_route_without_language_uses_accept_language_header() -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2023/1",
        headers={"Accept-Language": "de-DE, en;q=0.5"},
    ).raise_for_status()
    event: Final = EventResponseV1.model_validate(response.json())

    assert event.language_details.language_tag == Language.get("de")
    assert event.language_details.is_language_fallback is False
    assert "accept-language" in response.headers["vary"].lower()


@pytest.mark.asyncio
@pytest.mark.parametrize("language", ["en_US", "not a tag", "abc-123"])
async def test_event_route_handles_invalid_language_like_an_unavailable_one(language: str) -> None:
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}/v1/event/2023/1",
        params={"language": language},
        headers={"Accept-Language": "de"},
    ).raise_for_status()
    event: Final = EventResponseV1.model_validate(response.json())

    assert event.language_details.language_tag == Language.get("de")
    assert event.language_details.is_language_fallback is True
