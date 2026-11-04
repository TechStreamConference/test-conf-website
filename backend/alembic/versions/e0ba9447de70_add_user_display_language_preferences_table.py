"""add user_display_language_preferences table

Revision ID: e0ba9447de70
Revises: eafe415ff317
Create Date: 2026-11-01 17:38:01.746246

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e0ba9447de70"
down_revision: str | Sequence[str] | None = "eafe415ff317"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_display_language_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("language_tag", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["language_tag"], ["content_languages.tag"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_display_language_preferences")
