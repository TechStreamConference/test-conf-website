"""Selection of the language that translated content is delivered in."""

import re
from collections.abc import Collection
from collections.abc import Iterable
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final

from backend.content_languages import ENGLISH_LANGUAGE_TAG
from backend.models.content_language_types import ContentLanguageTag

# Bounds the work spent on a client-provided language range, independently of
# the supported syntax.
_MAX_LANGUAGE_RANGE_LENGTH = 64

# The supported subset of BCP 47: a primary language subtag, optionally followed
# by a script and a region subtag. Extended language, variant, extension and
# private-use subtags are deliberately not supported. The character classes are
# spelled out because `re.IGNORECASE` would let `[a-z]` match non-ASCII letters.
_LANGUAGE_RANGE_PATTERN = re.compile(r"([A-Za-z]{2,3})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?")


@final
class ContentLanguageSelection(NamedTuple):
    language_tag: ContentLanguageTag
    # Sorted, so that responses don’t depend on the order of database rows.
    available_languages: list[ContentLanguageTag]
    is_language_fallback: bool


def _primary_language_subtag(language_range: str) -> Optional[str]:
    if len(language_range) > _MAX_LANGUAGE_RANGE_LENGTH:
        return None
    match: Final = _LANGUAGE_RANGE_PATTERN.fullmatch(language_range)
    return None if match is None else match.group(1).lower()


def is_supported_language_range(language_range: str) -> bool:
    """Return whether a client-provided language range matches the supported syntax."""
    return _primary_language_subtag(language_range) is not None


def select_content_language(
    language_ranges: Iterable[str],
    available_languages: Collection[ContentLanguageTag],
) -> ContentLanguageSelection:
    """
    Select the language to deliver content in, using restricted RFC 4647 Lookup.

    `language_ranges` are the client’s preferences, most preferred first. Ranges
    that don’t match the supported syntax are ignored. Lookup tries each range and
    removes trailing subtags until an available language matches. Since content is
    stored per primary language only, this amounts to comparing primary language
    subtags case-insensitively. If no preference matches, English is selected if it
    is available, and otherwise the lexicographically first available language.

    The selection is a fallback if the client’s first supported preference wasn’t
    satisfied. Without any supported preference, it is not.
    """
    if not available_languages:
        raise ValueError("At least one language must be available.")

    sorted_languages: Final = sorted(available_languages)
    has_unsatisfied_preference = False
    for language_range in language_ranges:
        primary_language = _primary_language_subtag(language_range)
        if primary_language is None:
            continue
        if primary_language in available_languages:
            return ContentLanguageSelection(primary_language, sorted_languages, has_unsatisfied_preference)
        has_unsatisfied_preference = True

    default_language: Final = (
        ENGLISH_LANGUAGE_TAG if ENGLISH_LANGUAGE_TAG in available_languages else sorted_languages[0]
    )
    return ContentLanguageSelection(default_language, sorted_languages, has_unsatisfied_preference)
