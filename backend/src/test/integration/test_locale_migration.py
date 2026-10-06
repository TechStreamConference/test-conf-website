from datetime import UTC
from datetime import datetime
from datetime import timedelta
from typing import Final
from uuid import UUID

import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic.runtime.migration import MigrationContext

from alembic import command

pytestmark: Final = pytest.mark.integration

_PREVIOUS_REVISION = "a9b90a5b14e5"
_REVISION = "deadb21c674d"

# 65 characters; shortening drops the value of the `tz` keyword.
_LONG_LOCALE = "de-DE-u-ca-gregory-co-phonebk-hc-h23-kf-upper-kn-nu-latn-tz-deber"
_SHORTENED_LOCALE = "de-DE-u-ca-gregory-co-phonebk-hc-h23-kf-upper-kn-nu-latn-tz"
_SUGGESTION_ID = UUID("00000000-0000-0000-0000-000000000001")

_USERS = sa.table("users", sa.column("id"), sa.column("created_at"))
_USER_PREFERENCES = sa.table("user_preferences", sa.column("user_id"), sa.column("timezone"), sa.column("locale"))
_SESSIONS = sa.table(
    "sessions",
    sa.column("id"),
    sa.column("user_id"),
    sa.column("token_hash"),
    sa.column("created_at"),
    sa.column("last_seen_at"),
    sa.column("expires_at"),
    sa.column("absolute_expires_at"),
)
_REPORTED_REGIONAL_SETTINGS = sa.table(
    "reported_regional_settings",
    sa.column("session_id"),
    sa.column("timezone"),
    sa.column("locale"),
    sa.column("reported_at"),
)
_REGIONAL_SETTINGS_SUGGESTIONS = sa.table(
    "regional_settings_suggestions",
    sa.column("id"),
    sa.column("session_id"),
    sa.column("timezone"),
    sa.column("locale"),
    sa.column("created_at"),
)


@pytest.fixture
def database(migration_database: tuple[Config, sa.Engine]) -> sa.Engine:
    """Provide an empty database at the revision before the shortening."""
    config, engine = migration_database
    if _revision(engine) is None:
        command.upgrade(config, _PREVIOUS_REVISION)
    else:
        command.downgrade(config, _PREVIOUS_REVISION)
    with engine.begin() as connection:
        for table in (
            _REGIONAL_SETTINGS_SUGGESTIONS,
            _REPORTED_REGIONAL_SETTINGS,
            _SESSIONS,
            _USER_PREFERENCES,
            _USERS,
        ):
            _ = connection.execute(sa.delete(table))
    return engine


def _insert(engine: sa.Engine, *, preference_locales: list[str], session_locale: str) -> None:
    now: Final = datetime.now(UTC)
    with engine.begin() as connection:
        for user_id, locale in enumerate(preference_locales, start=1):
            _ = connection.execute(sa.insert(_USERS).values(id=user_id, created_at=now))
            _ = connection.execute(
                sa.insert(_USER_PREFERENCES).values(user_id=user_id, timezone="Europe/Berlin", locale=locale)
            )
        _ = connection.execute(
            sa.insert(_SESSIONS).values(
                id=1,
                user_id=1,
                token_hash="hash",
                created_at=now,
                last_seen_at=now,
                expires_at=now + timedelta(days=1),
                absolute_expires_at=now + timedelta(days=1),
            )
        )
        _ = connection.execute(
            sa.insert(_REPORTED_REGIONAL_SETTINGS).values(
                session_id=1, timezone="Europe/Berlin", locale=session_locale, reported_at=now
            )
        )
        _ = connection.execute(
            sa.insert(_REGIONAL_SETTINGS_SUGGESTIONS).values(
                id=_SUGGESTION_ID, session_id=1, timezone=None, locale=session_locale, created_at=now
            )
        )


def _locales(engine: sa.Engine) -> tuple[dict[int, str], str, str]:
    with engine.connect() as connection:
        preference_locales: Final[dict[int, str]] = dict(
            connection.execute(sa.select(_USER_PREFERENCES.c.user_id, _USER_PREFERENCES.c.locale)).tuples().all()
        )
        reported_locale: Final = connection.execute(sa.select(_REPORTED_REGIONAL_SETTINGS.c.locale)).scalar_one()
        suggested_locale: Final = connection.execute(sa.select(_REGIONAL_SETTINGS_SUGGESTIONS.c.locale)).scalar_one()
    return preference_locales, reported_locale, suggested_locale


def _revision(engine: sa.Engine) -> str | None:
    with engine.connect() as connection:
        return MigrationContext.configure(connection).get_current_revision()


def test_upgrade_shortens_long_locales_and_downgrade_keeps_them(
    migration_database: tuple[Config, sa.Engine],
    database: sa.Engine,
) -> None:
    config: Final = migration_database[0]
    _insert(database, preference_locales=[_LONG_LOCALE, "en-US"], session_locale=_LONG_LOCALE)

    command.upgrade(config, _REVISION)

    expected: Final = ({1: _SHORTENED_LOCALE, 2: "en-US"}, _SHORTENED_LOCALE, _SHORTENED_LOCALE)
    assert _locales(database) == expected

    command.downgrade(config, _PREVIOUS_REVISION)

    assert _locales(database) == expected


def test_upgrade_fails_without_changes_on_locales_that_cannot_be_shortened(
    migration_database: tuple[Config, sa.Engine],
    database: sa.Engine,
) -> None:
    config: Final = migration_database[0]
    # Stored before locales were validated: no prefix is valid, since already the first subtag is not.
    unshortenable: Final = "de_DE" + _LONG_LOCALE.removeprefix("de-DE")
    _insert(database, preference_locales=[unshortenable], session_locale=_LONG_LOCALE)
    locales_before: Final = _locales(database)

    with pytest.raises(RuntimeError, match=r"user_preferences: cannot shorten the locale for 1$"):
        command.upgrade(config, _REVISION)

    # Not even the shortenable locales were rewritten.
    assert _locales(database) == locales_before
    assert _revision(database) == _PREVIOUS_REVISION
