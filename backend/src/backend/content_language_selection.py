"""Selection of the language that translated content is delivered in."""

import re
from collections.abc import Collection
from collections.abc import Iterable
from typing import Annotated
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final

from fastapi import Query
from fastapi import Request
from fastapi import Response
from fastapi import status
from werkzeug.datastructures import LanguageAccept
from werkzeug.http import parse_accept_header

from backend.content_languages import ENGLISH_LANGUAGE_TAG
from backend.models.content_language_types import ContentLanguageTag
from backend.models.responses import UnsupportedLanguageTagResponseV1
from backend.utils import create_http_exception

# Bounds the work spent on a client-provided language range, independently of
# the supported syntax.
_MAX_LANGUAGE_RANGE_LENGTH = 64

# Bound the work spent on a client-provided `Accept-Language` header. A longer
# header is ignored entirely, and only the most preferred entries are considered.
_MAX_ACCEPT_LANGUAGE_LENGTH = 2048
_MAX_ACCEPT_LANGUAGE_ENTRIES = 32

# The supported subset of BCP 47: a primary language subtag, optionally followed
# by a script and a region subtag. Extended language, variant, extension and
# private-use subtags are deliberately not supported. The character classes are
# spelled out because `re.IGNORECASE` would let `[a-z]` match non-ASCII letters.
_LANGUAGE_RANGE_PATTERN = re.compile(r"([A-Za-z]{2,3})(?:-[A-Za-z]{4})?(?:-(?:[A-Za-z]{2}|[0-9]{3}))?")


# OpenAPI description of the headers on a successful response with translated content.
CONTENT_LANGUAGE_RESPONSE_HEADERS = {
    "Content-Language": {
        "description": "The language of the delivered content.",
        "schema": {"type": "string"},
    },
    "Vary": {
        "description": "Contains `Accept-Language` if no `language` query parameter was given.",
        "schema": {"type": "string"},
    },
}


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


def parse_accept_language(accept_language: str) -> list[str]:
    """
    Return the language ranges of an `Accept-Language` header, most preferred first.

    Entries are sorted by descending quality, keeping the client’s order on ties.
    Entries with an invalid quality and entries with `q=0` are dropped. A header
    longer than 2 KiB is ignored entirely, and at most 32 entries are returned.
    The ranges themselves aren’t validated; the selection skips unsupported ones.
    """
    # Starlette decodes header values as Latin-1, so every character stands for exactly
    # one byte of the header, even if it isn’t ASCII.
    if len(accept_language) > _MAX_ACCEPT_LANGUAGE_LENGTH:
        return []
    # werkzeug already sorts the entries by descending quality, keeping the client’s
    # order on ties. It sorts `*` last, which the selection skips anyway.
    entries: Final = parse_accept_header(accept_language, LanguageAccept)
    language_ranges: Final = [language_range for language_range, quality in entries if quality > 0.0]
    return language_ranges[:_MAX_ACCEPT_LANGUAGE_ENTRIES]


def get_requested_language_ranges(
    request: Request,
    response: Response,
    language: Annotated[
        Optional[str],
        Query(
            description=(
                "The preferred content language, e.g. `de` or `de-AT`. "
                + "It is matched by its primary language subtag. "
                + "Without it, the language is negotiated from the `Accept-Language` header."
            ),
        ),
    ] = None,
) -> list[str]:
    """
    Return the client’s content language preferences, most preferred first.

    An explicit `language` query parameter takes precedence and must match the
    supported syntax. Otherwise, the preferences come from the `Accept-Language`
    header, and the response varies by it, even if the request has none. The
    header’s value is never logged.
    """
    if language is not None:
        if not is_supported_language_range(language):
            raise create_http_exception(
                status.HTTP_422_UNPROCESSABLE_CONTENT,
                UnsupportedLanguageTagResponseV1(),
            )
        return [language]

    response.headers.add_vary_header("Accept-Language")
    # A header may be split across several field lines, which are combined with commas.
    return parse_accept_language(", ".join(request.headers.getlist("Accept-Language")))
