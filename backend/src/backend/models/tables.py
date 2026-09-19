from datetime import date
from datetime import datetime
from enum import StrEnum
from enum import auto
from typing import Optional
from typing import final

from sqlmodel import Field
from sqlmodel import SQLModel

from backend.utils import utc_now


class _AuditMixin(SQLModel):
    created_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
    )

    updated_at: datetime = Field(
        default_factory=utc_now,
        nullable=False,
        sa_column_kwargs={"onupdate": utc_now},
    )


@final
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)


@final
class Account(SQLModel, table=True):
    """The login-capable identity for a user. Not every user has one; "virtual"
    users (no login ability) exist only as a row in `users`.
    """

    __tablename__ = "accounts"  # type: ignore[reportAssignmentType]

    user_id: int = Field(foreign_key="users.id", primary_key=True)
    zitadel_user_id: str = Field(unique=True, nullable=False)
    email: str
    username: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)


@final
class UserSession(SQLModel, table=True):
    __tablename__ = "sessions"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", nullable=False)
    token_hash: str = Field(unique=True, nullable=False)
    # TODO: not used yet; will identify the ZITADEL session for back-channel logout.
    zitadel_session_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    last_seen_at: datetime = Field(default_factory=utc_now, nullable=False)
    expires_at: datetime
    absolute_expires_at: datetime
    revoked_at: Optional[datetime] = None


@final
class OidcLoginTransaction(SQLModel, table=True):
    __tablename__ = "oidc_login_transactions"  # type: ignore[reportAssignmentType]

    state_hash: str = Field(primary_key=True)
    browser_secret_hash: str
    nonce: str  # Raw: Authlib needs the original to validate the ID token claim.
    pkce_code_verifier: str  # Raw: sent verbatim to the token endpoint.
    return_to: str
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
    expires_at: datetime


# WARNING: Changing the `GlobalKey` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class GlobalKey(StrEnum):
    FOOTER_TEXT = auto()


@final
class Global(SQLModel, table=True):
    __tablename__ = "globals"  # type: ignore[reportAssignmentType]

    key: GlobalKey = Field(primary_key=True)
    value: str


# WARNING: Changing the `StaticPageKind` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class StaticPageKind(StrEnum):
    IMPRINT = auto()


@final
class StaticPage(SQLModel, table=True):
    __tablename__ = "static_pages"  # type: ignore[reportAssignmentType]

    kind: StaticPageKind = Field(primary_key=True)
    content: str


@final
class Event(_AuditMixin, table=True):
    __tablename__ = "events"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    start_date: date
    end_date: date
    discord_url: Optional[str]
    twitch_url: Optional[str]
    youtube_channel_url: Optional[str]
    publish_date: Optional[datetime]
    call_for_papers_start: Optional[datetime]
    call_for_papers_end: Optional[datetime]
    frontpage_spotlight_date: Optional[datetime]
    speakers_visible_from: Optional[datetime]
    sponsors_visible_from: Optional[datetime]
    media_partners_visible_from: Optional[datetime]
    team_members_visible_from: Optional[datetime]
    schedule_visible_from: Optional[datetime]


@final
class EventTranslation(_AuditMixin, table=True):
    __tablename__ = "event_translations"  # type: ignore[reportAssignmentType]

    event_id: int = Field(foreign_key="events.id", primary_key=True)
    language_tag: str = Field(primary_key=True)  # Following BCP 47.
    title: str
    subtitle: str
    presskit_url: Optional[str]
    trailer_url: Optional[str]
    trailer_poster_url: Optional[str]
    trailer_subtitles_url: Optional[str]
    description_headline: str
    description: str
