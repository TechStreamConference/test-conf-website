"""normalize display language tags

Revision ID: 33bb3322c275
Revises: 0f7cecbb7aa0
Create Date: 2026-10-05 22:19:33.408582

"""

from collections import defaultdict
from collections.abc import Sequence
from typing import Final
from typing import NamedTuple
from typing import final

import sqlalchemy as sa
from langcodes import Language
from langcodes import tag_is_valid
from sqlalchemy.types import UserDefinedType

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "33bb3322c275"
down_revision: str | Sequence[str] | None = "0f7cecbb7aa0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


@final
class StaticPageKind(UserDefinedType[str]):
    """The `staticpagekind` enum, without a fixed list of values that would have to match the values at this revision.

    Unlike the types of plain strings, parameters of this type are not cast to `VARCHAR` by the psycopg dialect, which
    PostgreSQL cannot compare with an enum. They are passed untyped and inferred as `staticpagekind` instead.
    """

    cache_ok = True

    def get_col_spec(self) -> str:
        return "staticpagekind"


# The display language columns are loaded as `langcodes.Language` objects from now on and written in their normalized
# spelling, so SQL comparisons only match if the stored tags are normalized as well.
STATIC_PAGES = sa.table(
    "static_pages",
    sa.column("kind", StaticPageKind()),
    sa.column("language_tag", sa.String),
)
EVENT_TRANSLATIONS = sa.table(
    "event_translations",
    sa.column("event_id", sa.Integer),
    sa.column("language_tag", sa.String),
)
# Each table maps to the column that identifies a row together with `language_tag`.
TABLES = {STATIC_PAGES: STATIC_PAGES.c.kind, EVENT_TRANSLATIONS: EVENT_TRANSLATIONS.c.event_id}


@final
class TagUpdate(NamedTuple):
    owner: object
    old_tag: str
    new_tag: str


def normalize_tag(tag: str) -> str:
    """Normalize a stored tag, rejecting it under the same rules the application applies when loading it.

    Deliberately duplicates `backend.language_tags.parse_language()` instead of importing it, so this migration keeps
    its behavior when the application code changes.
    """
    try:
        valid = "_" not in tag and tag_is_valid(tag)
    except ValueError:
        valid = False
    if not valid:
        raise ValueError(tag)
    return Language.get(tag).to_tag()


def plan_tag_updates(table: str, rows: Sequence[tuple[object, str]]) -> list[TagUpdate]:
    """Determine the tags to rewrite, or fail without changes if a tag is invalid or two tags would collide."""
    problems: Final[list[str]] = []
    tags_by_normalized_key: Final[defaultdict[tuple[object, str], list[str]]] = defaultdict(list)
    for owner, tag in rows:
        try:
            tags_by_normalized_key[owner, normalize_tag(tag)].append(tag)
        except ValueError:
            problems.append(f"{table}: invalid language tag {tag!r} for {owner!r}")

    updates: Final[list[TagUpdate]] = []
    for (owner, normalized), tags in tags_by_normalized_key.items():
        if len(tags) > 1:
            problems.append(f"{table}: language tags {sorted(tags)!r} for {owner!r} all normalize to {normalized!r}")
        elif tags[0] != normalized:
            updates.append(TagUpdate(owner=owner, old_tag=tags[0], new_tag=normalized))

    # The rows are updated one after another, so a tag must not be rewritten to a tag that another row still has before
    # its own update. This can only happen if normalizing a normalized tag changes it again.
    rewritten_tags: Final = {(update.owner, update.old_tag) for update in updates}
    for update in updates:
        if (update.owner, update.new_tag) in rewritten_tags:
            problems.append(
                f"{table}: language tag {update.old_tag!r} for {update.owner!r} normalizes to {update.new_tag!r}, "
                + "which is normalized differently itself"
            )

    if problems:
        raise RuntimeError("Cannot normalize display language tags:\n" + "\n".join(problems))
    return updates


def upgrade() -> None:
    """Rewrite all display language tags in their normalized spelling."""
    connection: Final = op.get_bind()
    updates_by_table: Final[dict[sa.TableClause, list[TagUpdate]]] = {}
    # Check every table before changing anything, so that a problem is reported completely.
    for table, owner_column in TABLES.items():
        rows = connection.execute(sa.select(owner_column, table.c.language_tag)).tuples().all()
        updates_by_table[table] = plan_tag_updates(table.name, rows)

    for table, updates in updates_by_table.items():
        owner_column = TABLES[table]
        for update in updates:
            _ = connection.execute(
                sa
                .update(table)
                .where(owner_column == update.owner, table.c.language_tag == update.old_tag)
                .values(language_tag=update.new_tag)
            )


def downgrade() -> None:
    """Keep the normalized tags.

    The original spellings cannot be restored, and normalized tags are valid for the previous revision as well.
    """
