from datetime import UTC
from datetime import datetime
from typing import Annotated
from typing import Final
from typing import Literal
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from langcodes import Language
from sqlalchemy import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import extract
from sqlmodel import select

from backend.database import get_session
from backend.models.responses import EventNotFoundResponseV1
from backend.models.responses import EventResponseV1
from backend.models.responses import InvalidSequenceNumberResponseV1
from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/{language_tag}/event",
    summary="Get the current event",
    description="Retrieve the event that is currently featured on the front page.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": EventNotFoundResponseV1},
    },
    operation_id="get current event v1",
)
async def get_current_event(
    session: Annotated[AsyncSession, Depends(get_session)],
    language_tag: str,
) -> EventResponseV1:
    now: Final = datetime.now(UTC).replace(tzinfo=None)
    current_event_id: Final = (
        select(Event.id)
        .where(
            col(Event.frontpage_spotlight_date).is_not(None),
            col(Event.frontpage_spotlight_date) <= now,
        )
        .order_by(
            col(Event.frontpage_spotlight_date).desc(),
            col(Event.start_date).desc(),
            col(Event.id).desc(),
        )
        .limit(1)
        .scalar_subquery()
    )
    statement: Final = (
        select(Event, EventTranslation)
        .join(
            EventTranslation,
            col(EventTranslation.event_id) == col(Event.id),
        )
        .where(col(Event.id) == current_event_id)
        .order_by(col(EventTranslation.language_tag))
    )
    rows: Final = list((await session.execute(statement)).all())

    return _event_response_v1_from_rows(rows, language_tag)


@ROUTER.get(
    "/{language_tag}/event/{year}/{sequence_number}",
    summary="Get event by year and sequence number",
    description="Retrieve a specific event based on the provided year and sequence number.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": InvalidSequenceNumberResponseV1},
        status.HTTP_404_NOT_FOUND: {"model": EventNotFoundResponseV1},
    },
    operation_id="get event by year and sequence number v1",
)
async def get_event_by_year_and_sequence_number(
    session: Annotated[AsyncSession, Depends(get_session)],
    language_tag: str,
    year: int,
    sequence_number: int | Literal["latest"],
) -> EventResponseV1:
    if isinstance(sequence_number, int) and sequence_number <= 0:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidSequenceNumberResponseV1(),
        )

    statement: Final = (
        select(Event, EventTranslation)
        .join(
            EventTranslation,
            col(EventTranslation.event_id) == col(Event.id),
        )
        .where(extract("year", col(Event.start_date)) == year)
        .order_by(
            col(Event.start_date),
            col(EventTranslation.language_tag),
        )
    )
    rows: Final = list((await session.execute(statement)).all())

    current_sequence_number = 0
    last_event_id: Optional[int] = None
    current_rows: Final[list[Row[tuple[tuple[Event, EventTranslation]]]]] = []
    for row in rows:
        if last_event_id is None or last_event_id != row.Event.id:
            last_event_id = row.Event.id
            if current_sequence_number == sequence_number:
                return _event_response_v1_from_rows(
                    current_rows,
                    language_tag,
                )
            current_sequence_number += 1
            current_rows.clear()

        current_rows.append(row)

    if sequence_number == current_sequence_number or sequence_number == "latest":
        return _event_response_v1_from_rows(
            current_rows,
            language_tag,
        )

    raise create_http_exception(
        status.HTTP_404_NOT_FOUND,
        EventNotFoundResponseV1(),
    )


def _event_response_v1_from_rows(
    rows: list[Row[tuple[tuple[Event, EventTranslation]]]],
    language_tag: str,
) -> EventResponseV1:
    if not rows:
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            EventNotFoundResponseV1(),
        )

    # All rows have the same data for the actual event (everything except
    # for things that have to be translated). Thus, we can just take the first
    # row and take all the basic data from that record.
    event: Final = rows[0].Event
    translations_by_language_tag: Final = {row.EventTranslation.language_tag: row.EventTranslation for row in rows}

    translation = translations_by_language_tag.get(language_tag)
    is_language_fallback: Final = translation is None

    # If the translation is missing, we first try to fall back to English.
    # Only if that is not available, we fall back to the first available
    # translation.
    if translation is None:
        translation = translations_by_language_tag.get(str(Language.get("en")))
    if translation is None:
        translation = next(iter(translations_by_language_tag.values()))

    return EventResponseV1(
        id=event.id,
        available_languages=list(translations_by_language_tag),
        language_tag=translation.language_tag,
        is_language_fallback=is_language_fallback,
        title=translation.title,
        subtitle=translation.subtitle,
        presskit_url=translation.presskit_url,
        trailer_url=translation.trailer_url,
        trailer_poster_url=translation.trailer_poster_url,
        trailer_subtitles_url=translation.trailer_subtitles_url,
        description_headline=translation.description_headline,
        description=translation.description,
        start_date=event.start_date,
        end_date=event.end_date,
        discord_url=event.discord_url,
        twitch_url=event.twitch_url,
        youtube_channel_url=event.youtube_channel_url,
        call_for_papers_start=event.call_for_papers_start,
        call_for_papers_end=event.call_for_papers_end,
        speakers_visible_from=event.speakers_visible_from,
        sponsors_visible_from=event.sponsors_visible_from,
        media_partners_visible_from=event.media_partners_visible_from,
        team_members_visible_from=event.team_members_visible_from,
        schedule_visible_from=event.schedule_visible_from,
    )
