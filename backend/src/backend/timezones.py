"""Validation and comparison of IANA timezone identifiers."""

import importlib.resources
from collections.abc import Mapping
from functools import cache
from typing import Annotated
from typing import Final
from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError
from zoneinfo import available_timezones

from pydantic import AfterValidator

# The timezones and their aliases are loaded only once, on first use, since loading them reads the timezone database.


@cache
def _iana_timezones() -> frozenset[str]:
    return frozenset(available_timezones())


@cache
def _timezone_aliases() -> Mapping[str, str]:
    """Map each IANA alias to its canonical zone name.

    `zoneinfo` has no public API for this: two `ZoneInfo` instances for
    aliased keys (for example "Asia/Istanbul" and "Europe/Istanbul") are
    neither `==` nor `is` to each other. The `tzdata` package ships the raw
    zic input file, whose "L <target> <alias>" lines are the same Link
    records that produce those aliases, so we parse it once.
    """
    aliases: Final[dict[str, str]] = {}
    zi_file: Final = importlib.resources.files("tzdata.zoneinfo").joinpath("tzdata.zi")
    with zi_file.open("r", encoding="ascii") as file:
        for line in file:
            if line.startswith("L "):
                _, target, alias = line.split()
                aliases[alias] = target
    return aliases


def canonical_timezone(value: str) -> str:
    """Resolve an IANA timezone identifier to its canonical (non-alias) form."""
    return _timezone_aliases().get(value, value)


def timezones_equivalent(a: str, b: str) -> bool:
    """Compare two IANA timezone identifiers by canonical zone, not by spelling
    or current UTC offset: distinct zones may temporarily share an offset and
    later diverge because of daylight-saving or political changes.
    """
    return canonical_timezone(a) == canonical_timezone(b)


def validate_timezone(value: str) -> str:
    """Validate an IANA timezone identifier while preserving its spelling."""
    # Some system zoneinfo installations expose host-specific convenience files
    # that are not timezone identifiers from the IANA database.
    if value in {"localtime", "posixrules"} or value.startswith(("posix/", "right/")) or value not in _iana_timezones():
        raise ValueError("Timezone must be a valid IANA timezone identifier.")
    try:
        _ = ZoneInfo(value)
    except (ValueError, ZoneInfoNotFoundError) as error:
        raise ValueError("Timezone must be a valid IANA timezone identifier.") from error
    return value


type IanaTimezone = Annotated[str, AfterValidator(validate_timezone)]
