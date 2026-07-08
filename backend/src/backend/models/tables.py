from datetime import UTC
from datetime import date
from datetime import datetime
from enum import StrEnum
from enum import auto
from typing import Optional
from typing import final

from sqlmodel import Field
from sqlmodel import SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)


class _AuditMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=_utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=_utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": _utc_now},
    )


@final
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utc_now, nullable=False)


# WARNING: Changing the `GlobalKey` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class GlobalKey(StrEnum):
    FOOTER_TEXT = auto()
    IMPRINT_TEXT = auto()


@final
class Global(SQLModel, table=True):
    __tablename__ = "globals"  # type: ignore[reportAssignmentType]

    key: GlobalKey = Field(primary_key=True)
    value: str


@final
class Event(_AuditMixin, table=True):
    __tablename__ = "events"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    subtitle: str
    start_date: date
    end_date: date
    discord_url: Optional[str]
    twitch_url: Optional[str]
    presskit_url: Optional[str]
    youtube_channel_url: Optional[str]
    trailer_url: Optional[str]
    trailer_poster_url: Optional[str]
    trailer_subtitles_url: Optional[str]
    description_headline: str
    description: str
    publish_date: Optional[datetime]
    call_for_papers_start: Optional[datetime]
    call_for_papers_end: Optional[datetime]
    frontpage_spotlight_date: Optional[datetime]
    speakers_visible_from: Optional[datetime]
    sponsors_visible_from: Optional[datetime]
    media_partners_visible_from: Optional[datetime]
    team_members_visible_from: Optional[datetime]
    schedule_visible_from: Optional[datetime]
