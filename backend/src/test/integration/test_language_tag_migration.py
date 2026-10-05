from collections.abc import Generator
from datetime import UTC
from datetime import date
from datetime import datetime
from pathlib import Path
from typing import Final

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from testcontainers.community.postgres import PostgresContainer

from alembic import command

pytestmark: Final = pytest.mark.integration

_MIGRATIONS_PATH = Path(__file__).resolve().parents[3] / "alembic"
_PREVIOUS_REVISION = "0f7cecbb7aa0"
_REVISION = "33bb3322c275"
_RENAME_REVISION = "a9b90a5b14e5"


@pytest.fixture(scope="module")
def migration_database() -> Generator[tuple[Config, sa.Engine]]:
    # A separate database, so that the shared, seeded one stays untouched.
    container: Final = PostgresContainer("postgres:16-alpine")
    _ = container.start()
    try:
        config: Final = Config()
        config.set_main_option("script_location", str(_MIGRATIONS_PATH))
        config.set_main_option("sqlalchemy.url", container.get_connection_url())
        engine: Final = sa.create_engine(container.get_connection_url())
        try:
            yield config, engine
        finally:
            engine.dispose()
    finally:
        container.stop()


@pytest.fixture
def database(migration_database: tuple[Config, sa.Engine]) -> sa.Engine:
    """Provide an empty database at the revision before the normalization."""
    config, engine = migration_database
    if _revision(engine) is None:
        command.upgrade(config, _PREVIOUS_REVISION)
    else:
        command.downgrade(config, _PREVIOUS_REVISION)
    with engine.begin() as connection:
        _ = connection.execute(sa.text("DELETE FROM event_translations"))
        _ = connection.execute(sa.text("DELETE FROM events"))
        _ = connection.execute(sa.text("DELETE FROM static_pages"))
    return engine


_STATIC_PAGES = sa.table("static_pages", sa.column("kind"), sa.column("language_tag"), sa.column("content"))
_EVENTS = sa.table(
    "events",
    sa.column("id"),
    sa.column("start_date"),
    sa.column("end_date"),
    sa.column("created_at"),
    sa.column("updated_at"),
)
_EVENT_TRANSLATIONS = sa.table(
    "event_translations",
    sa.column("event_id"),
    sa.column("language_tag"),
    sa.column("title"),
    sa.column("subtitle"),
    sa.column("description_headline"),
    sa.column("description"),
    sa.column("created_at"),
    sa.column("updated_at"),
)


def _insert(engine: sa.Engine, *, static_page_tags: list[str], event_translation_tags: list[tuple[int, str]]) -> None:
    now: Final = datetime.now(UTC)
    day: Final = date(2026, 9, 1)
    with engine.begin() as connection:
        for tag in static_page_tags:
            _ = connection.execute(sa.insert(_STATIC_PAGES).values(kind="IMPRINT", language_tag=tag, content="Imprint"))
        for event_id in sorted({event_id for event_id, _ in event_translation_tags}):
            _ = connection.execute(
                sa.insert(_EVENTS).values(id=event_id, start_date=day, end_date=day, created_at=now, updated_at=now)
            )
        for event_id, tag in event_translation_tags:
            _ = connection.execute(
                sa.insert(_EVENT_TRANSLATIONS).values(
                    event_id=event_id,
                    language_tag=tag,
                    title="Title",
                    subtitle="Subtitle",
                    description_headline="Headline",
                    description="Description",
                    created_at=now,
                    updated_at=now,
                )
            )


def _tags(engine: sa.Engine, *, column: str = "language_tag") -> tuple[set[str], set[tuple[int, str]]]:
    static_pages: Final = sa.table("static_pages", sa.column(column))
    event_translations: Final = sa.table("event_translations", sa.column("event_id"), sa.column(column))
    with engine.connect() as connection:
        static_page_tags: Final = set(connection.execute(sa.select(static_pages.c[column])).scalars())
        event_translation_tags: Final = {
            (event_id, tag)
            for event_id, tag in connection.execute(
                sa.select(event_translations.c.event_id, event_translations.c[column])
            ).tuples()
        }
    return static_page_tags, event_translation_tags


def _primary_key(engine: sa.Engine, table: str) -> list[str]:
    with engine.connect() as connection:
        primary_key: Final = sa.inspect(connection).get_pk_constraint(table)
    return list(primary_key["constrained_columns"])


def _revision(engine: sa.Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_upgrade_normalizes_tags_and_downgrade_keeps_them(
    migration_database: tuple[Config, sa.Engine],
    database: sa.Engine,
) -> None:
    config: Final = migration_database[0]
    engine: Final = database
    _insert(
        engine,
        static_page_tags=["de", "EN-us"],
        event_translation_tags=[(1, "de-de"), (1, "en"), (2, "DE-DE")],
    )

    command.upgrade(config, _REVISION)

    expected: Final = ({"de", "en-US"}, {(1, "de-DE"), (1, "en"), (2, "de-DE")})
    assert _tags(engine) == expected

    command.downgrade(config, _PREVIOUS_REVISION)

    assert _tags(engine) == expected


@pytest.mark.parametrize(
    ("static_page_tags", "event_translation_tags", "message"),
    [
        pytest.param(
            ["de-de", "de-DE"],
            [(1, "en-us")],
            r"static_pages: language tags \['de-DE', 'de-de'\] for 'IMPRINT' all normalize to 'de-DE'",
            id="collision",
        ),
        pytest.param(
            ["de-de"],
            [(1, "en_US")],
            r"event_translations: invalid language tag 'en_US' for 1",
            id="invalid tag",
        ),
    ],
)
def test_upgrade_fails_without_changes_on_problematic_tags(
    migration_database: tuple[Config, sa.Engine],
    database: sa.Engine,
    static_page_tags: list[str],
    event_translation_tags: list[tuple[int, str]],
    message: str,
) -> None:
    config: Final = migration_database[0]
    engine: Final = database
    _insert(engine, static_page_tags=static_page_tags, event_translation_tags=event_translation_tags)
    tags_before: Final = _tags(engine)

    with pytest.raises(RuntimeError, match=message):
        command.upgrade(config, _REVISION)

    # Not even the unproblematic tags were rewritten.
    assert _tags(engine) == tags_before
    assert _revision(engine) == _PREVIOUS_REVISION


def test_rename_keeps_tags_and_primary_keys(migration_database: tuple[Config, sa.Engine], database: sa.Engine) -> None:
    config: Final = migration_database[0]
    _insert(database, static_page_tags=["de", "en-US"], event_translation_tags=[(1, "de"), (1, "en")])
    expected: Final = ({"de", "en-US"}, {(1, "de"), (1, "en")})

    command.upgrade(config, _RENAME_REVISION)

    assert _tags(database, column="language") == expected
    assert _primary_key(database, "static_pages") == ["kind", "language"]
    assert _primary_key(database, "event_translations") == ["event_id", "language"]

    command.downgrade(config, _REVISION)

    assert _tags(database) == expected
    assert _primary_key(database, "static_pages") == ["kind", "language_tag"]
    assert _primary_key(database, "event_translations") == ["event_id", "language_tag"]
