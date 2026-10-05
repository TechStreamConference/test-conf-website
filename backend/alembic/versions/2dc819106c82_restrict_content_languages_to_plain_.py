"""restrict content languages to plain language subtags

Revision ID: 2dc819106c82
Revises: a9b90a5b14e5
Create Date: 2026-10-06 00:15:38.891286

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2dc819106c82"
down_revision: str | Sequence[str] | None = "a9b90a5b14e5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# The language selection only truncates the requested tag, never the stored ones, so translated content must be stored
# under plain language subtags (e.g. `de` instead of `de-DE`) to be found.
TABLES = ("static_pages", "event_translations")


def upgrade() -> None:
    """Restrict the display language columns to plain, normalized language subtags.

    Fails if a stored tag has further subtags, since it cannot be shortened without possibly merging translations.
    """
    for table in TABLES:
        op.create_check_constraint(f"ck_{table}_language_without_subtags", table, "language ~ '^[a-z]{2,3}$'")


def downgrade() -> None:
    """Allow any display language tag again."""
    for table in TABLES:
        op.drop_constraint(f"ck_{table}_language_without_subtags", table, type_="check")
