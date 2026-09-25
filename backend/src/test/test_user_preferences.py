from typing import Final
from typing import Optional

import pytest

from backend.config import SETTINGS
from backend.models.requests import UserPreferencesInputV1
from backend.models.tables import UserPreferences
from backend.user_preferences import RegionalSettingsReportOutcome
from backend.user_preferences import canonical_locale
from backend.user_preferences import canonical_timezone
from backend.user_preferences import categorize_field_outcome
from backend.user_preferences import locales_equivalent
from backend.user_preferences import process_regional_settings_report
from backend.user_preferences import resolve_effective_user_preferences
from backend.user_preferences import timezones_equivalent
from backend.user_preferences import validate_locale
from backend.user_preferences import validate_timezone


@pytest.mark.parametrize("timezone", ["Europe/Berlin", "Europe/Istanbul", "America/New_York"])
def test_valid_iana_timezones_are_accepted(timezone: str) -> None:
    assert validate_timezone(timezone) == timezone


@pytest.mark.parametrize("timezone", ["+02:00", "GMT+2", "localtime", "Europe/Does_Not_Exist", ""])
def test_invalid_timezones_are_rejected(timezone: str) -> None:
    with pytest.raises(ValueError, match="IANA"):
        _ = validate_timezone(timezone)


@pytest.mark.parametrize("locale", ["de-DE", "en", "en-US", "tr-TR", "haw", "zh-Hant-TW"])
def test_valid_bcp_47_locales_are_accepted_and_preserved(locale: str) -> None:
    # `haw` is valid but is not one of the languages currently seeded by the UI.
    assert validate_locale(locale) == locale
    assert UserPreferencesInputV1(timezone="Europe/Berlin", locale=locale).locale == locale


@pytest.mark.parametrize("locale", ["", "en_US", "en--US", "not a locale", "abc-123"])
def test_invalid_locales_are_rejected(locale: str) -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale(locale)


def test_effective_preferences_use_fallbacks_when_no_row_exists() -> None:
    effective: Final = resolve_effective_user_preferences(None)

    assert effective.timezone == SETTINGS.default_timezone == "Europe/Berlin"
    assert effective.locale == SETTINGS.default_locale == "en"


def test_effective_preferences_preserve_explicit_values_including_unsupported_locale() -> None:
    preferences: Final = UserPreferences(user_id=42, timezone="America/New_York", locale="haw")

    effective: Final = resolve_effective_user_preferences(preferences)

    assert effective.timezone == "America/New_York"
    assert effective.locale == "haw"


@pytest.mark.parametrize(
    ("alias", "canonical"),
    [
        ("Asia/Istanbul", "Europe/Istanbul"),
        ("Asia/Calcutta", "Asia/Kolkata"),
        ("Europe/Istanbul", "Europe/Istanbul"),
    ],
)
def test_canonical_timezone_resolves_known_aliases(alias: str, canonical: str) -> None:
    assert canonical_timezone(alias) == canonical


def test_timezones_equivalent_treats_aliases_as_equal() -> None:
    assert timezones_equivalent("Asia/Istanbul", "Europe/Istanbul")


def test_timezones_equivalent_does_not_use_current_utc_offset() -> None:
    # Berlin and Paris currently share an offset but have different histories
    # (for example, differing DST transition dates before EU unification).
    assert not timezones_equivalent("Europe/Berlin", "Europe/Paris")


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("en-us", "en-US"),
        ("EN-US", "en-US"),
        ("zh-Hant-TW", "zh-hant-tw"),
    ],
)
def test_locales_equivalent_ignores_casing(a: str, b: str) -> None:
    assert locales_equivalent(a, b)


def test_locales_equivalent_distinguishes_different_locales() -> None:
    assert not locales_equivalent("en-US", "en-GB")


def test_canonical_locale_normalizes_casing() -> None:
    assert canonical_locale("en-us") == "en-US"


def _report_outcome(
    *,
    reported_timezone: str = "Europe/Berlin",
    reported_locale: str = "en",
    previous_reported_timezone: Optional[str] = "Europe/Berlin",
    previous_reported_locale: Optional[str] = "en",
    preference_timezone: Optional[str] = "Europe/Berlin",
    preference_locale: Optional[str] = "en",
    suggested_timezone: Optional[str] = None,
    suggested_locale: Optional[str] = None,
) -> RegionalSettingsReportOutcome:
    return process_regional_settings_report(
        reported_timezone=reported_timezone,
        reported_locale=reported_locale,
        previous_reported_timezone=previous_reported_timezone,
        previous_reported_locale=previous_reported_locale,
        preference_timezone=preference_timezone,
        preference_locale=preference_locale,
        suggested_timezone=suggested_timezone,
        suggested_locale=suggested_locale,
    )


def test_first_report_initializes_a_missing_preference() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Tokyo",
        previous_reported_timezone=None,
        preference_timezone=None,
    )

    assert outcome.timezone.preference == "Asia/Tokyo"
    assert outcome.timezone.suggestion is None


def test_first_report_initializes_partial_preference_state_independently() -> None:
    # Timezone is already set, locale is not: only locale is initialized.
    outcome: Final = _report_outcome(
        reported_timezone="America/New_York",
        previous_reported_timezone=None,
        preference_timezone="Europe/Berlin",
        reported_locale="tr-TR",
        previous_reported_locale=None,
        preference_locale=None,
    )

    assert outcome.timezone.preference == "Europe/Berlin"
    assert outcome.timezone.suggestion == "America/New_York"
    assert outcome.locale.preference == "tr-TR"
    assert outcome.locale.suggestion is None


def test_first_report_equivalent_to_preference_does_not_create_a_suggestion() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Istanbul",
        previous_reported_timezone=None,
        preference_timezone="Europe/Istanbul",
    )

    assert outcome.timezone.preference == "Europe/Istanbul"
    assert outcome.timezone.suggestion is None


def test_repeated_equivalent_report_is_a_no_op_and_retains_state() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Europe/Berlin",
        previous_reported_timezone="Europe/Berlin",
        preference_timezone="America/New_York",
        suggested_timezone="Europe/Berlin",
    )

    assert outcome.is_no_op
    assert outcome.timezone.suggestion == "Europe/Berlin"
    assert outcome.timezone.preference == "America/New_York"


def test_report_differing_only_in_spelling_is_still_a_no_op() -> None:
    outcome: Final = _report_outcome(
        reported_locale="en-US",
        previous_reported_locale="en-us",
    )

    assert outcome.is_no_op


def test_in_sync_report_diverging_from_preference_creates_a_pending_suggestion() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Tokyo",
        previous_reported_timezone="Europe/Berlin",
        preference_timezone="Europe/Berlin",
    )

    assert not outcome.is_no_op
    assert outcome.timezone.preference == "Europe/Berlin"
    assert outcome.timezone.suggestion == "Asia/Tokyo"


def test_pending_suggestion_retains_its_spelling_for_an_equivalent_repeated_report() -> None:
    # The new report is a differently-spelled alias of the same zone as the
    # previous report, so it counts as equivalent and the existing
    # suggestion's own spelling is kept rather than overwritten.
    outcome: Final = _report_outcome(
        reported_timezone="Europe/Istanbul",
        previous_reported_timezone="Asia/Istanbul",
        preference_timezone="Europe/Berlin",
        suggested_timezone="Asia/Istanbul",
    )

    assert outcome.timezone.suggestion == "Asia/Istanbul"


def test_newer_differing_report_replaces_the_pending_suggestion() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Tokyo",
        previous_reported_timezone="Asia/Istanbul",
        preference_timezone="Europe/Berlin",
        suggested_timezone="Asia/Istanbul",
    )

    assert outcome.timezone.suggestion == "Asia/Tokyo"


def test_report_returning_to_the_preference_clears_a_pending_suggestion() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Europe/Berlin",
        previous_reported_timezone="Asia/Tokyo",
        preference_timezone="Europe/Berlin",
        suggested_timezone="Asia/Tokyo",
    )

    assert outcome.timezone.preference == "Europe/Berlin"
    assert outcome.timezone.suggestion is None


def test_dismissed_state_does_not_reprompt_for_an_equivalent_report() -> None:
    # No pending suggestion even though the report still differs from the
    # preference: a prior decision already dismissed it for this value.
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Istanbul",
        previous_reported_timezone="Europe/Istanbul",
        preference_timezone="Europe/Berlin",
        suggested_timezone=None,
    )

    assert outcome.timezone.suggestion is None


def test_dismissed_state_creates_a_new_suggestion_for_a_further_change() -> None:
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Tokyo",
        previous_reported_timezone="America/New_York",
        preference_timezone="Europe/Berlin",
        suggested_timezone=None,
    )

    assert outcome.timezone.suggestion == "Asia/Tokyo"


def test_timezone_and_locale_advance_independently() -> None:
    # The timezone report differs from its preference while the locale report
    # is equivalent to its own preference; only the timezone becomes pending.
    outcome: Final = _report_outcome(
        reported_timezone="Asia/Tokyo",
        previous_reported_timezone="Europe/Berlin",
        preference_timezone="Europe/Berlin",
        reported_locale="en-US",
        previous_reported_locale="en-GB",
        preference_locale="en-US",
    )

    assert not outcome.is_no_op
    assert outcome.timezone.suggestion == "Asia/Tokyo"
    assert outcome.locale.suggestion is None


@pytest.mark.parametrize(
    ("preference_was_missing", "previous_suggestion", "new_suggestion", "expected"),
    [
        (True, None, None, "initialized"),
        (False, None, None, "unchanged"),
        (False, "Europe/Berlin", None, "suggestion_cleared"),
        (False, None, "Asia/Tokyo", "suggestion_created"),
        (False, "Asia/Tokyo", "Asia/Tokyo", "unchanged"),
        (False, "Asia/Istanbul", "Asia/Tokyo", "suggestion_replaced"),
    ],
    ids=[
        "initializes-missing-preference",
        "stays-in-sync",
        "clears-existing-suggestion",
        "creates-new-suggestion",
        "retains-unchanged-suggestion",
        "replaces-differing-suggestion",
    ],
)
def test_categorize_field_outcome(
    preference_was_missing: bool,
    previous_suggestion: Optional[str],
    new_suggestion: Optional[str],
    expected: str,
) -> None:
    assert (
        categorize_field_outcome(
            preference_was_missing=preference_was_missing,
            previous_suggestion=previous_suggestion,
            new_suggestion=new_suggestion,
        )
        == expected
    )
