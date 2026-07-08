"""add `events` table

Revision ID: 0aa963f8102d
Revises: ac371c2e7891
Create Date: 2026-07-08 12:39:57.860129

"""

from collections.abc import Sequence

import sqlalchemy as sa
import sqlmodel

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0aa963f8102d"
down_revision: str | Sequence[str] | None = "ac371c2e7891"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "events",
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("subtitle", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("discord_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("twitch_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("presskit_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("youtube_channel_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_poster_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("trailer_subtitles_url", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("description_headline", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("publish_date", sa.DateTime(), nullable=True),
        sa.Column("call_for_papers_start", sa.DateTime(), nullable=True),
        sa.Column("call_for_papers_end", sa.DateTime(), nullable=True),
        sa.Column("frontpage_spotlight_date", sa.DateTime(), nullable=True),
        sa.Column("speakers_visible_from", sa.DateTime(), nullable=True),
        sa.Column("sponsors_visible_from", sa.DateTime(), nullable=True),
        sa.Column("media_partners_visible_from", sa.DateTime(), nullable=True),
        sa.Column("team_members_visible_from", sa.DateTime(), nullable=True),
        sa.Column("schedule_visible_from", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("events")
