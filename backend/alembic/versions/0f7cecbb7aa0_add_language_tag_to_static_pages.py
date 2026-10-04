"""add_language_tag_to_static_pages

Revision ID: 0f7cecbb7aa0
Revises: 4f4f56fef877
Create Date: 2026-10-02 20:07:36.418238

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0f7cecbb7aa0"
down_revision: str | Sequence[str] | None = "4f4f56fef877"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PRIMARY_KEY_NAME = "static_pages_pkey"
DEFAULT_LANGUAGE_TAG = "de"


def upgrade() -> None:
    """Upgrade schema."""
    # Existing rows receive the default language tag via the temporary server default.
    op.add_column(
        "static_pages",
        sa.Column(
            "language_tag",
            sqlmodel.sql.sqltypes.AutoString(),
            nullable=False,
            server_default=DEFAULT_LANGUAGE_TAG,
        ),
    )
    op.alter_column("static_pages", "language_tag", server_default=None)

    op.drop_constraint(PRIMARY_KEY_NAME, "static_pages", type_="primary")
    op.create_primary_key(PRIMARY_KEY_NAME, "static_pages", ["kind", "language_tag"])


def downgrade() -> None:
    """Downgrade schema."""
    # Only one page per kind can survive once `kind` is the sole primary key again.
    op.execute(
        sa.text("DELETE FROM static_pages WHERE language_tag <> :language_tag").bindparams(
            language_tag=DEFAULT_LANGUAGE_TAG
        )
    )
    op.drop_constraint(PRIMARY_KEY_NAME, "static_pages", type_="primary")
    op.drop_column("static_pages", "language_tag")
    op.create_primary_key(PRIMARY_KEY_NAME, "static_pages", ["kind"])
