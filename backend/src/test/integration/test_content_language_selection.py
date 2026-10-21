from collections.abc import AsyncGenerator
from datetime import date
from typing import Final

import pytest
import pytest_asyncio
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import delete

from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.routes.v1.events import get_event_by_year_and_sequence_number
from backend.routes.v1.imprint import get_imprint

pytestmark: Final = pytest.mark.integration

# No seeded event starts in this year.
_EVENT_YEAR = 2098


@pytest_asyncio.fixture
async def session(migrate_and_seed_database: str) -> AsyncGenerator[AsyncSession]:
    # Every test runs in a transaction that is rolled back, so that the seeded data stays untouched.
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    try:
        async with async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)() as session:
            try:
                yield session
            finally:
                await session.rollback()
    finally:
        await engine.dispose()


async def _delete_imprint_pages(session: AsyncSession, language_tags: list[str]) -> None:
    _ = await session.execute(
        delete(StaticPage).where(
            col(StaticPage.kind) == StaticPageKind.IMPRINT,
            col(StaticPage.language_tag).in_(language_tags),
        ),
    )


async def _add_event(session: AsyncSession, language_tags: list[str]) -> None:
    start_date: Final = date(_EVENT_YEAR, 5, 1)
    event: Final = Event(
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
    session.add(event)
    await session.flush()
    assert event.id is not None
    for language_tag in language_tags:
        session.add(
            EventTranslation(
                event_id=event.id,
                language_tag=language_tag,
                title=f"Title ({language_tag})",
                subtitle="",
                presskit_url=None,
                trailer_url=None,
                trailer_poster_url=None,
                trailer_subtitles_url=None,
                description_headline="",
                description="",
            ),
        )
        # Flush one by one, so that the rows are inserted in the given order.
        await session.flush()


@pytest.mark.asyncio
async def test_imprint_without_pages_is_not_found(session: AsyncSession) -> None:
    await _delete_imprint_pages(session, ["de", "en"])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_imprint(["de"], session)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_imprint_with_one_page_delivers_it(session: AsyncSession) -> None:
    await _delete_imprint_pages(session, ["en"])

    imprint: Final = await get_imprint(["en-GB"], session)

    assert imprint.language_details.available_languages == ["de"]
    assert imprint.language_details.language_tag == "de"
    assert imprint.language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language_ranges", "expected_language", "expected_fallback"),
    [
        pytest.param(["JA-jp"], "ja", False, id="regional request"),
        pytest.param(["de-AT"], "de", False, id="seeded language"),
        pytest.param(["fr"], "en", True, id="unavailable language"),
        pytest.param([], "en", False, id="no preference"),
    ],
)
async def test_imprint_with_several_pages_selects_by_lookup(
    session: AsyncSession,
    language_ranges: list[str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language_tag="ja", content="Imprint (ja)"))
    await session.flush()

    imprint: Final = await get_imprint(language_ranges, session)

    assert imprint.language_details.available_languages == ["de", "en", "ja"]
    assert imprint.language_details.language_tag == expected_language
    assert imprint.language_details.is_language_fallback is expected_fallback


@pytest.mark.asyncio
async def test_event_without_translations_is_not_found(session: AsyncSession) -> None:
    await _add_event(session, [])

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_event_by_year_and_sequence_number(session, ["de"], _EVENT_YEAR, 1)

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_event_with_one_translation_delivers_it(session: AsyncSession) -> None:
    await _add_event(session, ["ja"])

    event: Final = await get_event_by_year_and_sequence_number(session, ["de"], _EVENT_YEAR, 1)

    assert event.title == "Title (ja)"
    assert event.language_details.available_languages == ["ja"]
    assert event.language_details.language_tag == "ja"
    assert event.language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("language_ranges", "expected_language", "expected_fallback"),
    [
        pytest.param(["es-419"], "es", False, id="regional request"),
        pytest.param(["fr"], "de", True, id="first language without English"),
        pytest.param([], "de", False, id="no preference"),
    ],
)
async def test_event_with_several_translations_selects_by_lookup(
    session: AsyncSession,
    language_ranges: list[str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    await _add_event(session, ["ja", "es", "de"])

    event: Final = await get_event_by_year_and_sequence_number(session, language_ranges, _EVENT_YEAR, 1)

    assert event.title == f"Title ({expected_language})"
    assert event.language_details.available_languages == ["de", "es", "ja"]
    assert event.language_details.language_tag == expected_language
    assert event.language_details.is_language_fallback is expected_fallback
