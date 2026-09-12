"""add `oidc_login_transactions` table

Revision ID: 68f76dabaeaf
Revises: 48ada0771fab
Create Date: 2026-09-01 21:24:36.430082

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "68f76dabaeaf"
down_revision: str | Sequence[str] | None = "48ada0771fab"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "oidc_login_transactions",
        sa.Column("state_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("browser_secret_hash", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("nonce", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("pkce_code_verifier", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("return_to", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("state_hash"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("oidc_login_transactions")
