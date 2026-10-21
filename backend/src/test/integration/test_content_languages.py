from collections.abc import AsyncGenerator
from typing import Final

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import select

from backend.models.tables import ContentLanguage
from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind

pytestmark: Final = pytest.mark.integration


@pytest_asyncio.fixture
async def session_factory(migrate_and_seed_database: str) -> AsyncGenerator[async_sessionmaker[AsyncSession]]:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    try:
        yield async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    finally:
        await engine.dispose()


def _translation(event_id: int, language_tag: str) -> EventTranslation:
    return EventTranslation(
        event_id=event_id,
        language_tag=language_tag,
        title="Title",
        subtitle="Subtitle",
        presskit_url=None,
        trailer_url=None,
        trailer_poster_url=None,
        trailer_subtitles_url=None,
        description_headline="Headline",
        description="Description",
    )


async def _first_event_id(session: AsyncSession) -> int:
    event_id: Final = (await session.execute(select(Event.id).order_by(col(Event.id)).limit(1))).scalar_one()
    assert event_id is not None
    return event_id


@pytest.mark.asyncio
async def test_migration_inserts_the_snapshot_of_content_languages(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        tags: Final = set((await session.execute(select(ContentLanguage.tag))).scalars())

    assert {"de", "en", "es", "fil", "ja", "yue"} <= tags
    assert "und" not in tags
    assert all(tag.islower() and len(tag) in range(2, 4) for tag in tags)


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["ja", "fil", "yue", "pt", "uk"])
async def test_content_can_be_added_in_any_permitted_language(
    session_factory: async_sessionmaker[AsyncSession],
    language_tag: str,
) -> None:
    async with session_factory() as session:
        session.add(StaticPage(kind=StaticPageKind.IMPRINT, language_tag=language_tag, content="Imprint"))
        session.add(_translation(await _first_event_id(session), language_tag))
        await session.flush()
        await session.rollback()


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["xx", "DE", "de-AT", "und"])
async def test_static_pages_reject_languages_that_are_not_permitted(
    session_factory: async_sessionmaker[AsyncSession],
    language_tag: str,
) -> None:
    async with session_factory() as session:
        session.add(StaticPage(kind=StaticPageKind.IMPRINT, language_tag=language_tag, content="Imprint"))
        with pytest.raises(IntegrityError, match="static_pages_language_tag_fkey"):
            await session.flush()


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["xx", "DE", "de-AT", "und"])
async def test_event_translations_reject_languages_that_are_not_permitted(
    session_factory: async_sessionmaker[AsyncSession],
    language_tag: str,
) -> None:
    async with session_factory() as session:
        session.add(_translation(await _first_event_id(session), language_tag))
        with pytest.raises(IntegrityError, match="event_translations_language_tag_fkey"):
            await session.flush()


@pytest.mark.asyncio
@pytest.mark.parametrize("language_tag", ["DE", "de-AT", "d", "deut", "x1"])
async def test_content_languages_reject_malformed_tags(
    session_factory: async_sessionmaker[AsyncSession],
    language_tag: str,
) -> None:
    async with session_factory() as session:
        session.add(ContentLanguage(tag=language_tag))
        with pytest.raises(IntegrityError, match="ck_content_languages_tag_format"):
            await session.flush()


@pytest.mark.asyncio
async def test_referenced_content_languages_cannot_be_deleted(
    session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with session_factory() as session:
        with pytest.raises(IntegrityError, match="static_pages_language_tag_fkey|event_translations_language_tag_fkey"):
            _ = await session.execute(text("DELETE FROM content_languages WHERE tag = 'de'"))
