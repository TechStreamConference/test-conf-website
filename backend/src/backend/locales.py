"""Validation and comparison of BCP 47 locales."""

import itertools
import re
from typing import Annotated
from typing import Final

from pydantic import AfterValidator

# RFC 5646 recommends supporting tags of at least 35 characters, more leaves room for extensions and private use.
_MAX_LOCALE_LENGTH = 64

# Browsers only accept tags that are structurally valid according to ECMA-402 (`IsStructurallyValidLanguageTag`),
# i.e. Unicode BCP 47 locale identifiers (UTS #35) without their backwards compatibility syntax. This excludes
# POSIX-style underscores, grandfathered tags (`i-klingon`, `en-GB-oed`), extended language subtags (`zh-yue`), `root`,
# and tags consisting of private-use subtags only (`x-foo`), all of which make `Intl` APIs throw. The check is purely
# syntactic, so subtags don't have to be registered.
_LANGUAGE_SUBTAG = r"[a-z]{2,3}|[a-z]{5,8}"
_SCRIPT_SUBTAG = r"[a-z]{4}"
_REGION_SUBTAG = r"[a-z]{2}|[0-9]{3}"
_VARIANT_SUBTAG = r"[a-z0-9]{5,8}|[0-9][a-z0-9]{3}"
_LANGUAGE_ID = rf"(?:{_LANGUAGE_SUBTAG})(?:-{_SCRIPT_SUBTAG})?(?:-(?:{_REGION_SUBTAG}))?(?:-(?:{_VARIANT_SUBTAG}))*"
_KEYWORD = r"[a-z0-9][a-z](?:-[a-z0-9]{3,8})*"
_UNICODE_EXTENSION = rf"u(?:(?:-{_KEYWORD})+|(?:-[a-z0-9]{{3,8}})+(?:-{_KEYWORD})*)"
_TRANSFORMED_FIELD = r"[a-z][0-9](?:-[a-z0-9]{3,8})+"
_TRANSFORMED_EXTENSION = rf"t(?:-{_LANGUAGE_ID}(?:-{_TRANSFORMED_FIELD})*|(?:-{_TRANSFORMED_FIELD})+)"
_OTHER_EXTENSION = r"[0-9a-sv-wyz](?:-[a-z0-9]{2,8})+"
_PRIVATE_USE = r"x(?:-[a-z0-9]{1,8})+"
# Matched against the lowercase tag, which consists of ASCII characters only.
_LOCALE_ID_PATTERN = re.compile(
    rf"{_LANGUAGE_ID}(?:-(?:{_UNICODE_EXTENSION}|{_TRANSFORMED_EXTENSION}|{_OTHER_EXTENSION}))*(?:-{_PRIVATE_USE})?",
    re.ASCII,
)
_TRANSFORMED_FIELD_KEY_PATTERN = re.compile(r"[a-z][0-9]", re.ASCII)


def _variants(language_id_subtags: list[str]) -> list[str]:
    # Variants are the only subtags of a language ID after the language subtag with five or more characters or a
    # leading digit (scripts have four letters, regions two letters or three digits).
    return [
        subtag
        for subtag in language_id_subtags[1:]
        if len(subtag) >= 5 or (len(subtag) == 4 and subtag[0].isdigit())  # noqa: PLR2004
    ]


def _has_duplicates(subtags: list[str]) -> bool:
    return len(set(subtags)) != len(subtags)


def _is_structurally_valid(value: str) -> bool:
    """Check whether browsers accept `value` as a language tag, following
    ECMA-402's `IsStructurallyValidLanguageTag`.
    """
    # Checked before lowercasing, since some non-ASCII characters have an ASCII lowercase form (KELVIN SIGN, U+212A,
    # becomes `k`).
    if not value.isascii():
        return False
    lowercase: Final = value.lower()
    if _LOCALE_ID_PATTERN.fullmatch(lowercase) is None:
        return False
    # Every other subtag has at least two characters, so single-character subtags are exactly the singletons that
    # introduce extensions, and the first `x` introduces the private-use subtags, which are not checked for duplicates.
    all_subtags: Final = lowercase.split("-")
    subtags: Final = all_subtags[: all_subtags.index("x")] if "x" in all_subtags else all_subtags
    singleton_indices: Final = [index for index, subtag in enumerate(subtags) if len(subtag) == 1]
    if _has_duplicates([subtags[index] for index in singleton_indices]):
        return False
    extension_bounds: Final = [*singleton_indices, len(subtags)]
    if _has_duplicates(_variants(subtags[: extension_bounds[0]])):
        return False
    # The transformed extension (`t`) may start with a language ID, whose variants must not be duplicated either.
    for start, end in itertools.pairwise(extension_bounds):
        if subtags[start] == "t":
            transformed_language_id = list(
                itertools.takewhile(
                    lambda subtag: _TRANSFORMED_FIELD_KEY_PATTERN.fullmatch(subtag) is None,
                    subtags[start + 1 : end],
                ),
            )
            if _has_duplicates(_variants(transformed_language_id)):
                return False
    return True


def locales_equivalent(a: str, b: str) -> bool:
    """Compare two BCP 47 language tags case-insensitively.

    Tags are not canonicalized, so tags that only differ in other ways (e.g.
    `en-Latn-US` and `en-US`) are different. The frontend reports canonical
    locales (#414).
    """
    return a.lower() == b.lower()


def validate_locale(value: str) -> str:
    """Validate a BCP 47 language tag of at most `_MAX_LOCALE_LENGTH`
    characters that browsers accept, without canonicalizing it.
    """
    # The length is checked first, so overlong values are never matched against the pattern.
    if len(value) > _MAX_LOCALE_LENGTH or not _is_structurally_valid(value):
        raise ValueError("Locale must be a valid BCP 47 language tag.")
    return value


type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
