from datetime import date
from datetime import datetime
from typing import Literal
from typing import Optional
from typing import final
from uuid import UUID

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic import model_validator
from pydantic.alias_generators import to_camel

from backend.models.preference_types import Bcp47Locale
from backend.models.preference_types import IanaTimezone

# class name should include the api version since the typescript generator uses the same name.
# This could lead to confusion within the frontend once a second api version gets introduced.


class ApiResponseModel(BaseModel):
    """
    Base class for all API response models (success and error alike).

    Exposes fields as camelCase to the frontend while keeping snake_case field
    names in Python code.
    """

    model_config = ConfigDict(
        alias_generator=to_camel,
        validate_by_name=True,
        serialize_by_alias=True,
        field_title_generator=lambda name, info: name.replace("_", " ").title(),
    )


@final
class GlobalsResponseV1(ApiResponseModel):
    footer_text: str


@final
class ImprintResponseV1(ApiResponseModel):
    content: str
    available_languages: list[str]
    language_tag: str
    is_language_fallback: bool


@final
class ImprintPageContentNotFoundResponseV1(ApiResponseModel):
    detail: Literal["Imprint page not found in the database."] = "Imprint page not found in the database."


@final
class EventResponseV1(ApiResponseModel):
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
class EventNotFoundResponseV1(ApiResponseModel):
    detail: Literal["Event not found in the database."] = "Event not found in the database."


@final
class InvalidSequenceNumberResponseV1(ApiResponseModel):
    detail: Literal["Invalid sequence number."] = "Invalid sequence number."


@final
class InvalidRedirectUrlResponseV1(ApiResponseModel):
    detail: Literal["Invalid redirect URL."] = "Invalid redirect URL."


@final
class InvalidLoginTransactionResponseV1(ApiResponseModel):
    # Deliberately generic: an unknown, expired or mismatched transaction must not
    # be distinguishable from the outside.
    detail: Literal["Invalid or expired login transaction."] = "Invalid or expired login transaction."


@final
class IdentityProviderErrorResponseV1(ApiResponseModel):
    detail: Literal["The identity provider did not authenticate the user."] = (
        "The identity provider did not authenticate the user."
    )


@final
class EmailNotVerifiedResponseV1(ApiResponseModel):
    detail: Literal["The email address of this account is not verified."] = (
        "The email address of this account is not verified."
    )


@final
class LoginCallbackResponseV1(ApiResponseModel):
    redirect_url: str


@final
class NotAuthenticatedResponseV1(ApiResponseModel):
    detail: Literal["Not authenticated."] = "Not authenticated."


@final
class RegionalSettingsV1(ApiResponseModel):
    timezone: IanaTimezone
    locale: Bcp47Locale


@final
class RegionalSettingsChangeV1(ApiResponseModel):
    # At least one of `timezone`/`locale` is non-null: a null field means
    # there is no pending decision for that setting.
    id: UUID
    timezone: Optional[IanaTimezone]
    locale: Optional[Bcp47Locale]

    @model_validator(mode="after")
    def _require_at_least_one_change(self) -> "RegionalSettingsChangeV1":
        if self.timezone is None and self.locale is None:
            raise ValueError("At least one of `timezone` or `locale` must have changed.")
        return self


@final
class MeResponseV1(ApiResponseModel):
    id: int
    email: str
    username: str
    regional_settings: Optional[RegionalSettingsV1]
    regional_settings_change: Optional[RegionalSettingsChangeV1]


@final
class UserPreferencesResponseV1(ApiResponseModel):
    timezone: IanaTimezone
    locale: Bcp47Locale


@final
class RegionalSettingsChangeConflictResponseV1(ApiResponseModel):
    # Deliberately generic: an unknown, superseded, cross-session, or
    # already-decided suggestion ID must not be distinguishable from the
    # outside.
    detail: Literal["Invalid or outdated regional settings change."] = "Invalid or outdated regional settings change."
