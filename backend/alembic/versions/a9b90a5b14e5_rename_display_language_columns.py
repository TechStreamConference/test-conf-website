"""rename display language columns

Revision ID: a9b90a5b14e5
Revises: 33bb3322c275
Create Date: 2026-10-05 22:42:09.076910

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a9b90a5b14e5"
down_revision: str | Sequence[str] | None = "33bb3322c275"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The columns are loaded as `langcodes.Language` objects, so they are named after the language rather than its tag.
# Renaming keeps the data and the primary key constraints, which refer to the columns rather than their names.
TABLES = ("static_pages", "event_translations")


def upgrade() -> None:
    """Rename the display language columns from `language_tag` to `language`."""
    for table in TABLES:
        op.alter_column(table, "language_tag", new_column_name="language")


def downgrade() -> None:
    """Rename the display language columns back to `language_tag`."""
    for table in TABLES:
        op.alter_column(table, "language", new_column_name="language_tag")
