import pytest

from backend.timezones import canonical_timezone
from backend.timezones import timezones_equivalent
from backend.timezones import validate_timezone


@pytest.mark.parametrize("timezone", ["Europe/Berlin", "Europe/Istanbul", "America/New_York"])
def test_valid_iana_timezones_are_accepted(timezone: str) -> None:
    assert validate_timezone(timezone) == timezone


@pytest.mark.parametrize("timezone", ["+02:00", "GMT+2", "localtime", "Europe/Does_Not_Exist", ""])
def test_invalid_timezones_are_rejected(timezone: str) -> None:
    with pytest.raises(ValueError, match="IANA"):
        _ = validate_timezone(timezone)


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
