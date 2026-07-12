"""add `static_pages` table

Revision ID: 73b3c98b460f
Revises: 0e9b9a9c4ba8
Create Date: 2026-07-12 21:05:04.839319

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "73b3c98b460f"
down_revision: str | Sequence[str] | None = "0e9b9a9c4ba8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


key = sa.Enum("IMPRINT", name="staticpagekind")


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "static_pages",
        sa.Column("kind", key, nullable=False),
        sa.Column("content", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.PrimaryKeyConstraint("kind"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("static_pages")
    key.drop(op.get_bind())
    # ### end Alembic commands ###
