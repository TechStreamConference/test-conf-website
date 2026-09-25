"""add session regional settings reporting and suggestions

Revision ID: 4f4f56fef877
Revises: 5bfc312decfb
Create Date: 2026-09-21 21:28:41.011386

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f4f56fef877"
down_revision: str | Sequence[str] | None = "5bfc312decfb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "regional_settings_suggestions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("locale", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "timezone IS NOT NULL OR locale IS NOT NULL", name="ck_regional_settings_suggestions_non_empty"
        ),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_id"),
    )
    op.create_table(
        "reported_regional_settings",
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("timezone", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("locale", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("reported_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("session_id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("reported_regional_settings")
    op.drop_table("regional_settings_suggestions")
