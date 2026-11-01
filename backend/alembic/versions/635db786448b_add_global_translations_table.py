"""add global_translations table

Revision ID: 635db786448b
Revises: e0ba9447de70
Create Date: 2026-11-01 17:37:58.133195

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "635db786448b"
down_revision: str | Sequence[str] | None = "e0ba9447de70"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

GLOBAL_TRANSLATIONS_FOREIGN_KEY_NAME = "global_translations_language_tag_fkey"

# The existing enum type, which both tables share.
key = postgresql.ENUM("FOOTER_TEXT", name="globalkey", create_type=False)


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "global_translations",
        sa.Column("key", key, nullable=False),
        sa.Column("language_tag", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(
            ["language_tag"],
            ["content_languages.tag"],
            name=GLOBAL_TRANSLATIONS_FOREIGN_KEY_NAME,
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("key", "language_tag"),
    )
    # Existing values are dropped rather than carried over, since their language is unknown.
    op.drop_table("globals")


def downgrade() -> None:
    """Downgrade schema."""
    op.create_table(
        "globals",
        sa.Column("key", key, nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    op.drop_table("global_translations")
