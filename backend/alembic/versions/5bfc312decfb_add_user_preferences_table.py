"""add user preferences table

Revision ID: 5bfc312decfb
Revises: 4da74e4b07bb
Create Date: 2026-09-07 22:33:37.676924

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5bfc312decfb"
down_revision: str | Sequence[str] | None = "4da74e4b07bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "user_preferences",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("locale", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("user_preferences")
