"""Tests the data migration that gives every event and global value a translation in all supported languages."""

from collections.abc import Generator
from pathlib import Path
from typing import Final

import pytest
import sqlalchemy as sa
from alembic.config import Config
from testcontainers.community.postgres import PostgresContainer

from alembic import command

pytestmark = pytest.mark.integration

_MIGRATIONS_PATH = Path(__file__).resolve().parents[3] / "alembic"
_REVISION_BEFORE_THE_MIGRATION = "635db786448b"


@pytest.fixture
def alembic_config_and_engine() -> Generator[tuple[Config, sa.Engine]]:
    with PostgresContainer("postgres:16-alpine") as postgres:
        database_url: Final = postgres.get_connection_url(driver="psycopg")
        config: Final = Config()
        config.set_main_option("script_location", str(_MIGRATIONS_PATH))
        config.set_main_option("sqlalchemy.url", database_url)
        engine: Final = sa.create_engine(database_url)
        try:
            yield config, engine
        finally:
            engine.dispose()


def _insert_event(connection: sa.Connection, *languages: str) -> int:
    event_id: Final = connection.execute(
        sa.text(
            """
            INSERT INTO events (created_at, updated_at, start_date, end_date)
            VALUES (now(), now(), '2030-05-01', '2030-05-02')
            RETURNING id
            """,
        ),
    ).scalar_one()
    for language in languages:
        _ = connection.execute(
            sa.text(
                """
                INSERT INTO event_translations (
                    created_at, updated_at, event_id, language_tag, title, subtitle, description_headline, description
                )
                VALUES (now(), now(), :event_id, :language, :title, 'Subtitle', 'Headline', 'Description')
                """,
            ),
            {"event_id": event_id, "language": language, "title": f"Title ({language})"},
        )
    return event_id


def _event_titles(connection: sa.Connection, event_id: int) -> dict[str, str]:
    rows: Final = connection.execute(
        sa.text("SELECT language_tag, title FROM event_translations WHERE event_id = :event_id"),
        {"event_id": event_id},
    )
    return dict(rows.tuples().all())


def _insert_footer_text(connection: sa.Connection, *languages: str) -> None:
    for language in languages:
        _ = connection.execute(
            sa.text(
                "INSERT INTO global_translations (key, language_tag, value) VALUES ('FOOTER_TEXT', :language, :value)",
            ),
            {"language": language, "value": f"Footer ({language})"},
        )


def _footer_texts(connection: sa.Connection) -> dict[str, str]:
    rows: Final = connection.execute(sa.text("SELECT language_tag, value FROM global_translations"))
    return dict(rows.tuples().all())


def test_missing_event_translations_are_copied_from_english_or_the_first_language(
    alembic_config_and_engine: tuple[Config, sa.Engine],
) -> None:
    config, engine = alembic_config_and_engine
    command.upgrade(config, _REVISION_BEFORE_THE_MIGRATION)
    with engine.begin() as connection:
        only_english: Final = _insert_event(connection, "en")
        only_german: Final = _insert_event(connection, "de")
        only_spanish_and_japanese: Final = _insert_event(connection, "ja", "es")
        complete: Final = _insert_event(connection, "de", "en", "es")
        without_translations: Final = _insert_event(connection)

    command.upgrade(config, "head")

    with engine.begin() as connection:
        assert _event_titles(connection, only_english) == {"en": "Title (en)", "de": "Title (en)"}
        assert _event_titles(connection, only_german) == {"de": "Title (de)", "en": "Title (de)"}
        assert _event_titles(connection, only_spanish_and_japanese) == {
            "ja": "Title (ja)",
            "es": "Title (es)",
            "de": "Title (es)",
            "en": "Title (es)",
        }
        assert _event_titles(connection, complete) == {"de": "Title (de)", "en": "Title (en)", "es": "Title (es)"}
        assert _event_titles(connection, without_translations) == {}


def test_missing_global_value_translations_are_copied_from_the_first_language(
    alembic_config_and_engine: tuple[Config, sa.Engine],
) -> None:
    config, engine = alembic_config_and_engine
    command.upgrade(config, _REVISION_BEFORE_THE_MIGRATION)
    with engine.begin() as connection:
        _insert_footer_text(connection, "de", "ja")

    command.upgrade(config, "head")

    with engine.begin() as connection:
        assert _footer_texts(connection) == {
            "de": "Footer (de)",
            "ja": "Footer (ja)",
            "en": "Footer (de)",
        }
