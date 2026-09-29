"""store timestamps as timestamptz in UTC

Revision ID: 33ad77a904fb
Revises: 4da74e4b07bb
Create Date: 2026-09-29 18:35:48.419733

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "33ad77a904fb"
down_revision: str | Sequence[str] | None = "4da74e4b07bb"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# All existing naive values were written as UTC, so they are interpreted (and
# restored on downgrade) explicitly as UTC instead of the session's time zone.
_TIMESTAMP_COLUMNS: dict[str, tuple[str, ...]] = {
    "users": ("created_at",),
    "accounts": ("created_at",),
    "sessions": ("created_at", "last_seen_at", "expires_at", "absolute_expires_at", "revoked_at"),
    "oidc_login_transactions": ("created_at", "expires_at"),
    "events": (
        "created_at",
        "updated_at",
        "publish_date",
        "call_for_papers_start",
        "call_for_papers_end",
        "frontpage_spotlight_date",
        "speakers_visible_from",
        "sponsors_visible_from",
        "media_partners_visible_from",
        "team_members_visible_from",
        "schedule_visible_from",
    ),
    "event_translations": ("created_at", "updated_at"),
}


def upgrade() -> None:
    """Upgrade schema."""
    for table, columns in _TIMESTAMP_COLUMNS.items():
        with op.batch_alter_table(table) as batch_op:
            for column in columns:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(),
                    type_=sa.DateTime(timezone=True),
                    postgresql_using=f"{column} AT TIME ZONE 'UTC'",
                )


def downgrade() -> None:
    """Downgrade schema."""
    for table, columns in _TIMESTAMP_COLUMNS.items():
        with op.batch_alter_table(table) as batch_op:
            for column in columns:
                batch_op.alter_column(
                    column,
                    existing_type=sa.DateTime(timezone=True),
                    type_=sa.DateTime(),
                    postgresql_using=f"{column} AT TIME ZONE 'UTC'",
                )
