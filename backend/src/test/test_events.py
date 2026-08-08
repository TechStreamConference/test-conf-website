from datetime import date
from typing import Final
from typing import Literal
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from backend.models.responses import EventResponseV1
from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.routes.v1.events import get_event_by_year_and_sequence_number


def _event(event_id: int, start_date: date) -> Event:
    return Event(
        id=event_id,
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


def _translation(event_id: int, language_tag: str) -> EventTranslation:
    return EventTranslation(
        event_id=event_id,
        language_tag=language_tag,
        title=f"Title {event_id} ({language_tag})",
        subtitle="Subtitle",
        presskit_url=None,
        trailer_url=None,
        trailer_poster_url=None,
        trailer_subtitles_url=None,
        description_headline="Headline",
        description="Description",
    )


def _row(event: Event, translation: EventTranslation) -> Mock:
    row: Final = Mock()
    row.Event = event
    row.EventTranslation = translation
    return row


def _session_with_rows(rows: list[Mock]) -> AsyncMock:
    session: Final = AsyncMock()
    session.execute.return_value = Mock(all=Mock(return_value=rows))
    return session


@pytest.mark.asyncio
async def test_event_returns_requested_numbered_event_and_translation() -> None:
    first_event: Final = _event(1, date(2024, 5, 1))
    second_event: Final = _event(2, date(2024, 9, 1))
    session: Final = _session_with_rows([
        _row(first_event, _translation(1, "de")),
        _row(second_event, _translation(2, "de")),
        _row(second_event, _translation(2, "en")),
    ])

    result: Final = await get_event_by_year_and_sequence_number(session, "en", 2024, 2)

    assert isinstance(result, EventResponseV1)
    assert result.id == 2
    assert result.available_languages == ["de", "en"]
    assert result.language_tag == "en"
    assert result.is_language_fallback is False


@pytest.mark.asyncio
async def test_event_latest_falls_back_to_english() -> None:
    event: Final = _event(1, date(2024, 5, 1))
    session: Final = _session_with_rows([
        _row(event, _translation(1, "de")),
        _row(event, _translation(1, "en")),
    ])

    result: Final = await get_event_by_year_and_sequence_number(session, "fr", 2024, "latest")

    assert result.language_tag == "en"
    assert result.is_language_fallback is True


@pytest.mark.asyncio
async def test_event_falls_back_to_first_available_translation() -> None:
    event: Final = _event(1, date(2024, 5, 1))
    session: Final = _session_with_rows([_row(event, _translation(1, "de"))])

    result: Final = await get_event_by_year_and_sequence_number(session, "fr", 2024, 1)

    assert result.language_tag == "de"
    assert result.is_language_fallback is True


@pytest.mark.asyncio
async def test_event_rejects_invalid_sequence_number() -> None:
    session: Final = AsyncMock()

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_event_by_year_and_sequence_number(session, "de", 2024, 0)

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid sequence number."
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("sequence_number", [1, "latest"])
async def test_event_returns_not_found_when_no_event_exists(sequence_number: int | Literal["latest"]) -> None:
    session: Final = _session_with_rows([])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_event_by_year_and_sequence_number(session, "de", 2025, sequence_number)

    assert exc_info.value.status_code == 404
    assert exc_info.value.detail == "Event not found in the database."
