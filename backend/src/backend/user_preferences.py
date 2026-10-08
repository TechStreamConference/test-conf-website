from collections.abc import Callable
from enum import StrEnum
from enum import auto
from functools import cache
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final

from backend.config import SETTINGS
from backend.language_tags import standardize_language_tag
from backend.models.tables import UserPreferences
from backend.timezones import canonical_timezone


def canonical_locale(value: str) -> str:
    """Resolve a valid BCP 47 language tag, such as all stored and reported
    locales, to its canonical form (see `standardize_language_tag()`), so that
    locales are compared by canonical form, not raw spelling.
    """
    return standardize_language_tag(value)


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


@final
class _ReportedFieldOutcome(NamedTuple):
    is_repeated: bool
    """`True` when the reported value is equivalent to the session’s previous
    report."""

    observation: FieldObservationOutcome


def _process_reported_field(
    *,
    reported: str,
    previous_reported: Optional[str],
    preference: Optional[str],
    previous_suggestion: Optional[str],
    canonical: Callable[[str], str],
) -> _ReportedFieldOutcome:
    @cache
    def canonical_reported() -> str:
        return canonical(reported)

    def is_equivalent_to_reported(value: str) -> bool:
        # Canonicalizing a locale parses it, so the reported value is canonicalized at most once, and not at all if it
        # is spelled like the value that it is compared to.
        return value == reported or canonical(value) == canonical_reported()

    if previous_reported is not None and is_equivalent_to_reported(previous_reported):
        # Equivalent report: retain current preference and suggestion state.
        return _ReportedFieldOutcome(
            is_repeated=True,
            observation=FieldObservationOutcome(preference=preference, suggestion=previous_suggestion),
        )

    if preference is None:
        # Unreported -> InSync: first report initializes a missing preference.
        observation = FieldObservationOutcome(preference=reported, suggestion=None)
    elif is_equivalent_to_reported(preference):
        # (InSync|Pending|Dismissed) -> InSync: report now matches the preference.
        observation = FieldObservationOutcome(preference=preference, suggestion=None)
    else:
        # InSync -> Pending, or Pending/Dismissed -> Pending: report differs from
        # the preference. The preference itself does not move until decided.
        observation = FieldObservationOutcome(preference=preference, suggestion=reported)
    return _ReportedFieldOutcome(is_repeated=False, observation=observation)


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
    timezone: Final = _process_reported_field(
        reported=reported_timezone,
        previous_reported=previous_reported_timezone,
        preference=preference_timezone,
        previous_suggestion=suggested_timezone,
        canonical=canonical_timezone,
    )
    locale: Final = _process_reported_field(
        reported=reported_locale,
        previous_reported=previous_reported_locale,
        preference=preference_locale,
        previous_suggestion=suggested_locale,
        canonical=canonical_locale,
    )
    return RegionalSettingsReportOutcome(
        is_no_op=timezone.is_repeated and locale.is_repeated,
        timezone=timezone.observation,
        locale=locale.observation,
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
