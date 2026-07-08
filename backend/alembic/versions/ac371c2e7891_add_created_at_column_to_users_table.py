"""add `created_at` column to `users` table

Revision ID: ac371c2e7891
Revises: 88da587105f3
Create Date: 2026-07-08 12:37:15.136097

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "ac371c2e7891"
down_revision: str | Sequence[str] | None = "88da587105f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.alter_column("users", "created_at", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "created_at")
