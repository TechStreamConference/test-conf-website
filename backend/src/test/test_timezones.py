import importlib.resources
import zoneinfo
from collections.abc import Iterator
from pathlib import Path
from typing import Final

import pytest

from backend.timezones import _iana_timezones  # type: ignore[reportPrivateUsage]
from backend.timezones import canonical_timezone
from backend.timezones import timezones_equivalent
from backend.timezones import validate_timezone


@pytest.mark.parametrize("timezone", ["Europe/Berlin", "Europe/Istanbul", "America/New_York"])
def test_valid_iana_timezones_are_accepted(timezone: str) -> None:
    assert validate_timezone(timezone) == timezone


@pytest.mark.parametrize(
    "timezone",
    [
        "+02:00",
        "GMT+2",
        "localtime",
        "posixrules",
        "posix/Europe/Berlin",
        "right/Europe/Berlin",
        "Europe/Does_Not_Exist",
        "",
    ],
)
def test_invalid_timezones_are_rejected(timezone: str) -> None:
    with pytest.raises(ValueError, match="IANA"):
        _ = validate_timezone(timezone)


@pytest.fixture
def system_zoneinfo_with_special_files(tmp_path: Path) -> Iterator[Path]:
    """A system zoneinfo directory that, like the one of many Linux distributions, also contains the
    `posix/` and `right/` directories as well as the `posixrules` and `localtime` files.
    """
    berlin: Final = importlib.resources.files("tzdata.zoneinfo").joinpath("Europe", "Berlin").read_bytes()
    for key in ["Europe/Berlin", "posix/Europe/Berlin", "right/Europe/Berlin", "posixrules", "localtime"]:
        path = tmp_path / key
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_bytes(berlin)
    zoneinfo.reset_tzpath(to=[str(tmp_path)])
    _iana_timezones.cache_clear()
    yield tmp_path
    zoneinfo.reset_tzpath()
    _iana_timezones.cache_clear()


@pytest.mark.parametrize("timezone", ["localtime", "posixrules", "posix/Europe/Berlin", "right/Europe/Berlin"])
@pytest.mark.usefixtures("system_zoneinfo_with_special_files")
def test_special_files_of_the_system_zoneinfo_are_rejected(timezone: str) -> None:
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
