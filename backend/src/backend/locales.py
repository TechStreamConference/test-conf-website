"""Validation and comparison of BCP 47 locales."""

from typing import Annotated
from typing import Final

from langcodes import standardize_tag
from langcodes import tag_is_valid
from pydantic import AfterValidator


def canonical_locale(value: str) -> str:
    """Resolve a BCP 47 language tag to its canonical form (casing, redundant
    script/region subtags, deprecated subtag replacements).
    """
    return standardize_tag(value)


def locales_equivalent(a: str, b: str) -> bool:
    """Compare two BCP 47 language tags by canonical form, not raw spelling."""
    return canonical_locale(a) == canonical_locale(b)


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


type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
