"""add globals table

Revision ID: 0e9b9a9c4ba8
Revises: f2da44aefb1a
Create Date: 2026-06-28 13:24:58.961085

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0e9b9a9c4ba8"
down_revision: str | Sequence[str] | None = "f2da44aefb1a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


key = sa.Enum("FOOTER_TEXT", name="globalkey")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "globals",
        sa.Column("key", key, nullable=False),
        sa.Column("value", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("key"),
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("globals")
    key.drop(op.get_bind())
    # ### end Alembic commands ###
