"""IANA timezone identifiers.

Kept free of other backend imports, so that `backend.config` can validate its
settings with it as well.
"""

from zoneinfo import ZoneInfo
from zoneinfo import ZoneInfoNotFoundError
from zoneinfo import available_timezones

_IANA_TIMEZONES = available_timezones()


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
