from datetime import date
from datetime import datetime
from typing import Literal
from typing import Optional
from typing import final

from pydantic import BaseModel

# class name should include the api version since the typescript generator uses the same name.
# This could lead to confusion within the frontend once a second api version gets introduced.


@final
class GlobalsResponseV1(BaseModel):
    footer_text: str


@final
class ImprintResponseV1(BaseModel):
    content: str


@final
class ImprintPageContentNotFoundResponseV1(BaseModel):
    detail: Literal["Imprint page not found in the database."] = "Imprint page not found in the database."


@final
class EventResponseV1(BaseModel):
    id: int
    available_languages: list[str]
    language_tag: str
    is_language_fallback: bool
    title: str
    subtitle: str
    presskit_url: Optional[str]
    trailer_url: Optional[str]
    trailer_poster_url: Optional[str]
    trailer_subtitles_url: Optional[str]
    description_headline: str
    description: str
    start_date: date
    end_date: date
    discord_url: Optional[str]
    twitch_url: Optional[str]
    youtube_channel_url: Optional[str]
    call_for_papers_start: Optional[datetime]
    call_for_papers_end: Optional[datetime]
    speakers_visible_from: Optional[datetime]
    sponsors_visible_from: Optional[datetime]
    media_partners_visible_from: Optional[datetime]
    team_members_visible_from: Optional[datetime]
    schedule_visible_from: Optional[datetime]


@final
class EventNotFoundResponseV1(BaseModel):
    detail: Literal["Event not found in the database."] = "Event not found in the database."


@final
class InvalidSequenceNumberResponseV1(BaseModel):
    detail: Literal["Invalid sequence number."] = "Invalid sequence number."


@final
class InvalidRedirectUrlResponseV1(BaseModel):
    detail: Literal["Invalid redirect URL."] = "Invalid redirect URL."


@final
class InvalidLoginTransactionResponseV1(BaseModel):
    # Deliberately generic: an unknown, expired or mismatched transaction must not
    # be distinguishable from the outside.
    detail: Literal["Invalid or expired login transaction."] = "Invalid or expired login transaction."


@final
class IdentityProviderErrorResponseV1(BaseModel):
    detail: Literal["The identity provider did not authenticate the user."] = (
        "The identity provider did not authenticate the user."
    )


@final
class EmailNotVerifiedResponseV1(BaseModel):
    detail: Literal["The email address of this account is not verified."] = (
        "The email address of this account is not verified."
    )


@final
class LoginCallbackResponseV1(BaseModel):
    redirect_url: str


@final
class NotAuthenticatedResponseV1(BaseModel):
    detail: Literal["Not authenticated."] = "Not authenticated."


@final
class MeResponseV1(BaseModel):
    id: int
    email: str
    username: str
