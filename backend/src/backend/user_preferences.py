import importlib.resources
from collections.abc import Callable
from enum import StrEnum
from enum import auto
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError
from zoneinfo import available_timezones

from langcodes import standardize_tag
from langcodes import tag_is_valid

from backend.config import SETTINGS
from backend.models.tables import UserPreferences

_IANA_TIMEZONES = available_timezones()


def _load_timezone_aliases() -> dict[str, str]:
    """Map each IANA alias to its canonical zone name.

    `zoneinfo` has no public API for this: two `ZoneInfo` instances for
    aliased keys (for example "Asia/Istanbul" and "Europe/Istanbul") are
    neither `==` nor `is` to each other. The `tzdata` package ships the raw
    zic input file, whose "L <target> <alias>" lines are the same Link
    records that produce those aliases, so we parse it once at import time.
    """
    aliases: dict[str, str] = {}
    zi_file = importlib.resources.files("tzdata.zoneinfo").joinpath("tzdata.zi")
    with zi_file.open("r", encoding="ascii") as file:
        for line in file:
            if line.startswith("L "):
                _, target, alias = line.split()
                aliases[alias] = target
    return aliases


_TIMEZONE_ALIASES: Final = _load_timezone_aliases()


def canonical_timezone(value: str) -> str:
    """Resolve an IANA timezone identifier to its canonical (non-alias) form."""
    return _TIMEZONE_ALIASES.get(value, value)


def timezones_equivalent(a: str, b: str) -> bool:
    """Compare two IANA timezone identifiers by canonical zone, not by spelling
    or current UTC offset: distinct zones may temporarily share an offset and
    later diverge because of daylight-saving or political changes.
    """
    return canonical_timezone(a) == canonical_timezone(b)


def canonical_locale(value: str) -> str:
    """Resolve a BCP 47 language tag to its canonical form (casing, redundant
    script/region subtags, deprecated subtag replacements).
    """
    return standardize_tag(value)


def locales_equivalent(a: str, b: str) -> bool:
    """Compare two BCP 47 language tags by canonical form, not raw spelling."""
    return canonical_locale(a) == canonical_locale(b)


def validate_timezone(value: str) -> str:
    """Validate an IANA timezone identifier while preserving its spelling."""
    # Some system zoneinfo installations expose host-specific convenience files
    # that are not timezone identifiers from the IANA database.
    if value in {"localtime", "posixrules"} or value.startswith(("posix/", "right/")) or value not in _IANA_TIMEZONES:
        raise ValueError("Timezone must be a valid IANA timezone identifier.")
    try:
        _ = ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError("Timezone must be a valid IANA timezone identifier.") from error
    return value


def validate_locale(value: str) -> str:
    """Validate a browser-style BCP 47 language tag without canonicalizing it."""
    # langcodes also accepts POSIX-style underscores as a convenience, while
    # browser locale APIs require BCP 47's hyphen-separated representation.
    if "_" in value:
        raise ValueError("Locale must be a valid BCP 47 language tag.")
    try:
        valid: Final = tag_is_valid(value)
    except ValueError as error:
        raise ValueError("Locale must be a valid BCP 47 language tag.") from error
    if not valid:
        raise ValueError("Locale must be a valid BCP 47 language tag.")
    return value


@final
class EffectiveUserPreferences(NamedTuple):
    timezone: str
    locale: str


def resolve_effective_user_preferences(preferences: Optional[UserPreferences]) -> EffectiveUserPreferences:
    """Resolve preferences without changing the stored record."""
    return EffectiveUserPreferences(
        timezone=preferences.timezone if preferences is not None else SETTINGS.default_timezone,
        locale=preferences.locale if preferences is not None else SETTINGS.default_locale,
    )


@final
class FieldObservationOutcome(NamedTuple):
    """The result of advancing one field’s independent state machine (see
    the regional settings design doc) by one reported value."""

    preference: Optional[str]
    """The confirmed preference after processing: unchanged unless the field
    had no preference yet and is initialized by this report."""

    suggestion: Optional[str]
    """The pending suggestion candidate after processing, or `None` if there
    is no pending decision for this field."""


def _process_reported_field(
    *,
    reported: str,
    previous_reported: Optional[str],
    preference: Optional[str],
    previous_suggestion: Optional[str],
    equivalent: Callable[[str, str], bool],
) -> FieldObservationOutcome:
    if previous_reported is not None and equivalent(reported, previous_reported):
        # Equivalent report: retain current preference and suggestion state.
        return FieldObservationOutcome(preference=preference, suggestion=previous_suggestion)

    if preference is None:
        # Unreported -> InSync: first report initializes a missing preference.
        return FieldObservationOutcome(preference=reported, suggestion=None)

    if equivalent(reported, preference):
        # (InSync|Pending|Dismissed) -> InSync: report now matches the preference.
        return FieldObservationOutcome(preference=preference, suggestion=None)

    # InSync -> Pending, or Pending/Dismissed -> Pending: report differs from
    # the preference. The preference itself does not move until decided.
    return FieldObservationOutcome(preference=preference, suggestion=reported)


@final
class RegionalSettingsReportOutcome(NamedTuple):
    is_no_op: bool
    """`True` when both reported values are equivalent to the session’s
    previous report, so nothing must be written to the database."""

    timezone: FieldObservationOutcome
    locale: FieldObservationOutcome


def process_regional_settings_report(
    *,
    reported_timezone: str,
    reported_locale: str,
    previous_reported_timezone: Optional[str],
    previous_reported_locale: Optional[str],
    preference_timezone: Optional[str],
    preference_locale: Optional[str],
    suggested_timezone: Optional[str],
    suggested_locale: Optional[str],
) -> RegionalSettingsReportOutcome:
    """Pure state-machine step for one browser report. The caller loads and
    locks the current state and persists the result transactionally."""
    timezone_repeated: Final = previous_reported_timezone is not None and timezones_equivalent(
        reported_timezone,
        previous_reported_timezone,
    )
    locale_repeated: Final = previous_reported_locale is not None and locales_equivalent(
        reported_locale,
        previous_reported_locale,
    )
    return RegionalSettingsReportOutcome(
        is_no_op=timezone_repeated and locale_repeated,
        timezone=_process_reported_field(
            reported=reported_timezone,
            previous_reported=previous_reported_timezone,
            preference=preference_timezone,
            previous_suggestion=suggested_timezone,
            equivalent=timezones_equivalent,
        ),
        locale=_process_reported_field(
            reported=reported_locale,
            previous_reported=previous_reported_locale,
            preference=preference_locale,
            previous_suggestion=suggested_locale,
            equivalent=locales_equivalent,
        ),
    )


class RegionalSettingsFieldOutcomeCategory(StrEnum):
    UNCHANGED = auto()
    INITIALIZED = auto()
    SUGGESTION_CREATED = auto()
    SUGGESTION_REPLACED = auto()
    SUGGESTION_CLEARED = auto()


def categorize_field_outcome(
    *,
    preference_was_missing: bool,
    previous_suggestion: Optional[str],
    new_suggestion: Optional[str],
) -> RegionalSettingsFieldOutcomeCategory:
    """Categorize one field's outcome for operational logging.

    The returned label never contains a reported timezone or locale value
    itself, only which transition occurred.
    """
    if new_suggestion is None:
        if preference_was_missing:
            return RegionalSettingsFieldOutcomeCategory.INITIALIZED
        return (
            RegionalSettingsFieldOutcomeCategory.SUGGESTION_CLEARED
            if previous_suggestion is not None
            else RegionalSettingsFieldOutcomeCategory.UNCHANGED
        )
    if previous_suggestion is None:
        return RegionalSettingsFieldOutcomeCategory.SUGGESTION_CREATED
    return (
        RegionalSettingsFieldOutcomeCategory.UNCHANGED
        if new_suggestion == previous_suggestion
        else RegionalSettingsFieldOutcomeCategory.SUGGESTION_REPLACED
    )
