"""add `IMPRINT_TEXT` key to `globals` table

Revision ID: 88da587105f3
Revises: 0e9b9a9c4ba8
Create Date: 2026-07-08 10:54:45.647451

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "88da587105f3"
down_revision: str | Sequence[str] | None = "0e9b9a9c4ba8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE globalkey ADD VALUE 'IMPRINT_TEXT'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support DROP VALUE; the enum must be recreated.
    op.execute("DELETE FROM globals WHERE key = 'IMPRINT_TEXT'")
    op.execute("ALTER TABLE globals ALTER COLUMN key TYPE VARCHAR USING key::text")
    op.execute("DROP TYPE globalkey")
    op.execute("CREATE TYPE globalkey AS ENUM ('FOOTER_TEXT')")
    op.execute("ALTER TABLE globals ALTER COLUMN key TYPE globalkey USING key::globalkey")
