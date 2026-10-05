from collections.abc import AsyncGenerator
from typing import Final

import pytest
import pytest_asyncio
import sqlalchemy as sa
from langcodes import Language
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import select

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
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language=Language.get("en-us"), content="Howdy"))
    await session.flush()

    stored: Final = (
        await session.execute(sa.text("SELECT language FROM static_pages WHERE content = 'Howdy'"))
    ).scalar_one()

    assert stored == "en-US"


@pytest.mark.asyncio
async def test_invalid_stored_tags_fail_when_loading(session: AsyncSession) -> None:
    _ = await session.execute(
        sa.text("INSERT INTO static_pages (kind, language, content) VALUES ('IMPRINT', 'en_US', 'Broken')")
    )

    with pytest.raises(ValueError, match="BCP 47"):
        _ = (await session.execute(select(StaticPage).where(col(StaticPage.content) == "Broken"))).scalar_one()
