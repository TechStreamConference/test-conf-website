"""shorten locales exceeding the tag length limit

Revision ID: deadb21c674d
Revises: a9b90a5b14e5
Create Date: 2026-10-06 17:18:13.244240

"""

from collections.abc import Sequence
from typing import Final
from typing import NamedTuple
from typing import final

import sqlalchemy as sa
from langcodes import tag_is_valid

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "deadb21c674d"
down_revision: str | Sequence[str] | None = "a9b90a5b14e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Locales longer than this are rejected from now on, also when they are part of a response, so the stored ones are
# shortened. Each table maps to the column that identifies a row.
TABLES = {
    "user_preferences": "user_id",
    "reported_regional_settings": "session_id",
    "regional_settings_suggestions": "id",
}
MAX_TAG_LENGTH = 64


@final
class LocaleUpdate(NamedTuple):
    key: object
    new_locale: str


def is_valid_locale(locale: str) -> bool:
    """Duplicates the validation rules of `backend.language_tags.validate_locale()` instead of importing it, so this
    migration keeps its rules when the application code changes.
    """
    # `tag_is_valid()` returns `False` for tags that cannot be parsed instead of raising.
    return len(locale) <= MAX_TAG_LENGTH and "_" not in locale and tag_is_valid(locale)


def shorten_locale(locale: str) -> str:
    """Drop trailing subtags until the locale is valid again.

    The leading subtags determine the language and region, so the shortened locale still formats values like the
    original one in most respects (e.g. extension subtags selecting a calendar or collation are dropped first).
    """
    subtags: Final = locale.split("-")
    for length in range(len(subtags) - 1, 0, -1):
        candidate = "-".join(subtags[:length])
        if is_valid_locale(candidate):
            return candidate
    raise ValueError(locale)


def upgrade() -> None:
    """Shorten all stored locales that exceed the tag length limit."""
    connection: Final = op.get_bind()
    problems: Final[list[str]] = []
    updates_by_table: Final[dict[sa.TableClause, tuple[str, list[LocaleUpdate]]]] = {}
    # Check every table before changing anything, so that a problem is reported completely.
    for table_name, key_column in TABLES.items():
        table = sa.table(table_name, sa.column(key_column), sa.column("locale"))
        rows = connection.execute(
            sa.select(table.c[key_column], table.c.locale).where(sa.func.length(table.c.locale) > MAX_TAG_LENGTH)
        ).tuples()
        updates: list[LocaleUpdate] = []
        for key, locale in rows:
            try:
                updates.append(LocaleUpdate(key=key, new_locale=shorten_locale(locale)))
            except ValueError:
                # The locale itself is not reported, since it is personal data.
                problems.append(f"{table_name}: cannot shorten the locale for {key!r}")
        updates_by_table[table] = (key_column, updates)

    if problems:
        raise RuntimeError("Cannot shorten locales:\n" + "\n".join(problems))

    for table, (key_column, updates) in updates_by_table.items():
        for update in updates:
            _ = connection.execute(
                sa.update(table).where(table.c[key_column] == update.key).values(locale=update.new_locale)
            )


def downgrade() -> None:
    """Keep the shortened locales.

    The original locales cannot be restored, and shortened locales are valid for the previous revision as well.
    """
