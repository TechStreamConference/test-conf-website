from collections.abc import AsyncGenerator
from datetime import date
from typing import Final

import pytest
import pytest_asyncio
import sqlalchemy as sa
from langcodes import Language
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import select

from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind

pytestmark: Final = pytest.mark.integration


@pytest_asyncio.fixture
async def session(migrate_and_seed_database: str) -> AsyncGenerator[AsyncSession]:
    engine: Final = create_async_engine(migrate_and_seed_database)
    try:
        async with async_sessionmaker(bind=engine, class_=AsyncSession)() as session:
            try:
                yield session
            finally:
                # Leave the seeded data untouched for other tests.
                await session.rollback()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_seeded_language_tags_are_loaded_as_languages(session: AsyncSession) -> None:
    pages: Final = list((await session.execute(select(StaticPage))).scalars())

    assert {page.language for page in pages} == {Language.get("de"), Language.get("en")}
    assert all(isinstance(page.language, Language) for page in pages)


@pytest.mark.asyncio
async def test_queries_match_languages_in_any_spelling(session: AsyncSession) -> None:
    page: Final = (
        await session.execute(select(StaticPage).where(col(StaticPage.language) == Language.get("DE")))
    ).scalar_one()

    assert page.language == Language.get("de")


@pytest.mark.asyncio
async def test_languages_are_stored_in_normalized_spelling(session: AsyncSession) -> None:
    # `iw` is the deprecated subtag for Hebrew.
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language=Language.get("iw"), content="Shalom"))
    await session.flush()

    stored: Final = (
        await session.execute(sa.text("SELECT language FROM static_pages WHERE content = 'Shalom'"))
    ).scalar_one()

    assert stored == "he"


@pytest.mark.asyncio
async def test_invalid_stored_tags_fail_when_loading(session: AsyncSession) -> None:
    _ = await session.execute(
        # Unregistered, but shaped like a language subtag, so the database accepts it.
        sa.text("INSERT INTO static_pages (kind, language, content) VALUES ('IMPRINT', 'zz', 'Broken')")
    )

    with pytest.raises(ValueError, match="BCP 47"):
        _ = (await session.execute(select(StaticPage).where(col(StaticPage.content) == "Broken"))).scalar_one()


# Content is only found by the language selection if it is stored under a plain language subtag.
@pytest.mark.asyncio
@pytest.mark.parametrize("tag", ["de-DE", "zh-Hant", "en-x-private"])
async def test_content_languages_must_not_have_further_subtags(session: AsyncSession, tag: str) -> None:
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language=Language.get(tag), content="Regional"))

    with pytest.raises(IntegrityError, match="ck_static_pages_language_without_subtags"):
        await session.flush()


@pytest.mark.asyncio
async def test_event_translation_languages_must_not_have_further_subtags(session: AsyncSession) -> None:
    event_id: Final = (await session.execute(select(Event.id).limit(1))).scalar_one()
    session.add(
        EventTranslation(
            event_id=event_id,
            language=Language.get("de-DE"),
            title="",
            subtitle="",
            presskit_url=None,
            trailer_url=None,
            trailer_poster_url=None,
            trailer_subtitles_url=None,
            description_headline="",
            description="",
        )
    )

    with pytest.raises(IntegrityError, match="ck_event_translations_language_without_subtags"):
        await session.flush()


def _event_translation(event_id: int, tag: str) -> EventTranslation:
    return EventTranslation(
        event_id=event_id,
        language=Language.get(tag),
        title=tag,
        subtitle="",
        presskit_url=None,
        trailer_url=None,
        trailer_poster_url=None,
        trailer_subtitles_url=None,
        description_headline="",
        description="",
    )


# The unit of work sorts rows by their primary key when flushing several updates or deletes at once, which requires
# the `Language` part of the key to be orderable.
@pytest.mark.asyncio
async def test_several_translations_can_be_updated_and_deleted_at_once(session: AsyncSession) -> None:
    event: Final = Event(
        start_date=date(2099, 1, 1),
        end_date=date(2099, 1, 1),
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
    translations: Final = [_event_translation(event.id, tag) for tag in ["en", "de", "es"]]
    session.add_all(translations)
    await session.flush()

    for translation in translations:
        translation.title = "Changed"
    await session.flush()
    for translation in translations:
        await session.delete(translation)
    await session.flush()

    remaining: Final = (
        await session.execute(select(EventTranslation).where(col(EventTranslation.event_id) == event.id))
    ).all()
    assert remaining == []
