"""Selection of the language in which translated content is delivered.

The language is resolved in the following order:

1. the requested language (the `language` query parameter, if given and a
   valid BCP 47 tag),
2. the best available language from the `Accept-Language` header (respecting
   quality values),
3. English,
4. the first available language.

Languages match if they are the same written language, i.e. the same
language in the same (likely) script, regardless of region or variants: `de`,
`de-AT`, and `de-DE` all match each other, while `zh-TW` (Traditional) and
`zh-Hans` (Simplified) do not. Of several matching available languages, the
one sharing the longest prefix of subtags with the requested tag wins (so
`de-AT-1996` prefers `de-AT` over `de`), then the least specific one (so
`de-AT` prefers `de` over `de-DE`), then the first one. English is any
available language matching `en`.

The delivered language is marked as a fallback if the client's first choice
(the requested language or, if not given, the most preferred valid header
entry) is not available, i.e. no available language matches it. A requested
language that is not a valid BCP 47 tag is handled like an unavailable one
rather than failing the request, so a stale or malformed tag still delivers
content. If the client did not express
any preference at all, there is no first choice that could be missing, so
English or the first available language is not marked as a fallback.
"""

from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
from itertools import islice
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final

from fastapi import Response
from langcodes import Language
from werkzeug.datastructures import LanguageAccept
from werkzeug.http import parse_accept_header

from backend.language_tags import WrittenLanguage
from backend.language_tags import parse_language
from backend.language_tags import written_language
from backend.models.responses import LanguageDetailsV1

LANGUAGE_SELECTION_DESCRIPTION = (
    "The language is selected in the following order: the requested language (`language`, if given and a "
    + "valid BCP 47 tag; an invalid tag is handled like an unavailable language), "
    + "the best available language from the `Accept-Language` header (respecting quality values), "
    + "English, and finally the first available language. Languages match if they are the same language "
    + "in the same (likely) script, regardless of region or variants (e.g. `de-AT` matches `de` and `de-DE`, "
    + "but `zh-TW` does not match `zh-Hans`); the closest available tag is preferred. Wildcards and "
    + "languages excluded with `q=0` are ignored, so an excluded language may still be delivered as the "
    + "English or first available language. `isLanguageFallback` is `true` if the client's first choice "
    + "(`language` or, if not given, the most preferred valid `Accept-Language` entry) is not available, and "
    + "`false` if the client did not express any preference."
)

_ENGLISH = parse_language("en")

# Browsers send a handful of entries. Considering only the most preferred ones bounds the work a client can cause.
_MAX_ACCEPT_LANGUAGE_ENTRIES = 16

# Deliberately not validated as `Bcp47Language`: an invalid tag must not fail the request but is handled like an
# unavailable language, so a stale or malformed tag still delivers content.
type RequestedLanguageTag = str


@final
class _LanguageToBeDelivered(NamedTuple):
    language: Language
    is_language_fallback: bool
    varies_with_accept_language: bool
    """
    Indicates whether cached responses should be invalidated when
    the `Accept-Language` header of a subsequent request changes.

    See: https://www.rfc-editor.org/info/rfc9110/#field.vary
    """


@final
class SelectedTranslation[T](NamedTuple):
    translation: T
    language_details: LanguageDetailsV1


@final
class _AvailableLanguage(NamedTuple):
    language: Language
    written_language: WrittenLanguage
    subtags: list[str]


def _index_available_languages(available_languages: Sequence[Language]) -> list[_AvailableLanguage]:
    """Precompute what is needed for matching, once per selection rather than once per requested language."""
    index: Final[list[_AvailableLanguage]] = []
    for available in available_languages:
        available_written_language = written_language(available)
        # Tags without a language (`und`) do not match any requested language.
        if available_written_language is not None:
            index.append(
                _AvailableLanguage(
                    language=available,
                    written_language=available_written_language,
                    subtags=available.to_tag().split("-"),
                )
            )
    return index


def _common_prefix_length(a: Sequence[str], b: Sequence[str]) -> int:
    length = 0
    for subtag_a, subtag_b in zip(a, b, strict=False):
        if subtag_a != subtag_b:
            break
        length += 1
    return length


# werkzeug's `LanguageAccept.best_match()` is deliberately not used for matching, only for parsing the header:
# - It tries exact matches across all header entries before primary-subtag matches, so a less preferred exact match wins
#   (`de-AT, en;q=0.5` with `de-DE` and `en` available selects `en`).
# - It never matches sibling regions (`de-AT` does not find `de-DE`) and ignores likely scripts (`zh-TW`, i.e.
#   Traditional, finds `zh`, i.e. Simplified).
# - It compares spellings instead of canonical forms (`iw` does not find `he`) and lets wildcards match any language.
# - It only returns the matched value, so it cannot tell whether the client's first choice was available.
def _find_available_language(
    language: Language, available_languages: Sequence[_AvailableLanguage]
) -> Optional[Language]:
    """Return the available language that best matches `language`, or `None`
    if none is the same written language.

    Matching is symmetric (`de-DE` finds `de`, and `de` finds `de-DE`), see
    the module documentation for the preference among several matches.
    """
    requested_written_language: Final = written_language(language)
    if requested_written_language is None:
        return None
    requested_subtags: Final = language.to_tag().split("-")
    candidates: Final = [
        available for available in available_languages if available.written_language == requested_written_language
    ]
    if not candidates:
        return None
    # `min()` returns the first of several equally good candidates. The available object itself is returned (instead of
    # re-parsing the tag), so the result is usable as a key into the translations.
    return min(
        candidates,
        key=lambda available: (
            -_common_prefix_length(available.subtags, requested_subtags),
            len(available.subtags),
        ),
    ).language


def _parse_valid_language(tag: str) -> Optional[Language]:
    try:
        return parse_language(tag)
    except ValueError:
        return None


def _parse_accept_language_header(header: str) -> Iterator[Language]:
    """Yield the languages of an `Accept-Language` header, most preferred first.

    Entries are parsed lazily, so the selection stops parsing at the first
    available language. Only the `_MAX_ACCEPT_LANGUAGE_ENTRIES` most preferred
    entries are considered.

    Wildcards, excluded languages (`q=0`), and entries that are not valid BCP 47
    tags are skipped: the header is controlled by the client and an invalid
    entry must not make the whole request fail. Entries are validated like the
    requested language, so an invalid entry is never the client's first choice.

    Excluded languages are ignored rather than avoided, so the English or first
    available language may still be an excluded one: the content is always
    delivered instead of responding with 406 Not Acceptable.
    """
    # `LanguageAccept` is already sorted by quality (stable, so entries of equal quality keep their order), with
    # wildcards last.
    for tag, quality in islice(parse_accept_header(header, LanguageAccept), _MAX_ACCEPT_LANGUAGE_ENTRIES):
        if quality <= 0.0 or tag == "*":
            continue
        language = _parse_valid_language(tag)
        if language is not None:
            yield language


def _determine_language_to_be_delivered(
    *,
    language: Optional[RequestedLanguageTag],
    accept_language_header: Optional[str],
    available_languages: Sequence[Language],
) -> _LanguageToBeDelivered:
    if not available_languages:
        raise ValueError("At least one language must be available.")
    indexed_languages: Final = _index_available_languages(available_languages)

    # An invalid tag still expresses a preference, so it is handled like an unavailable language.
    requested_language: Final = None if language is None else _parse_valid_language(language)
    if requested_language is not None:
        available_route_language: Final = _find_available_language(requested_language, indexed_languages)
        if available_route_language is not None:
            return _LanguageToBeDelivered(
                language=available_route_language,
                is_language_fallback=False,
                varies_with_accept_language=False,
            )

    # TODO: Respect the language preference of logged-in users. Requires
    #       `https://github.com/TechStreamConference/test-conf-website/issues/387` to
    #       be resolved first.

    # Whether a more preferred valid header entry has been unavailable.
    header_expressed_preference = False
    if accept_language_header is not None:
        for header_language in _parse_accept_language_header(accept_language_header):
            available_header_language = _find_available_language(header_language, indexed_languages)
            if available_header_language is not None:
                return _LanguageToBeDelivered(
                    language=available_header_language,
                    is_language_fallback=language is not None or header_expressed_preference,
                    varies_with_accept_language=True,
                )
            header_expressed_preference = True

    # Without a requested language or a valid header entry, there is no first choice that could be missing.
    client_expressed_preference: Final = language is not None or header_expressed_preference
    english: Final = _find_available_language(_ENGLISH, indexed_languages)
    return _LanguageToBeDelivered(
        language=available_languages[0] if english is None else english,
        is_language_fallback=client_expressed_preference,
        varies_with_accept_language=True,
    )


def select_language(
    available_languages: Sequence[Language],
    *,
    language: Optional[RequestedLanguageTag],
    accept_language: Optional[str],
    response: Response,
) -> LanguageDetailsV1:
    """Select the language to be delivered and describe the selection.

    Adds `Vary: Accept-Language` to the response if the selection depends on
    that header. Raises `ValueError` if no language is available at all.
    """
    language_to_be_delivered: Final = _determine_language_to_be_delivered(
        language=language,
        accept_language_header=accept_language,
        available_languages=available_languages,
    )
    if language_to_be_delivered.varies_with_accept_language:
        # Caches must not serve this response to clients with a different `Accept-Language` header.
        response.headers.add_vary_header("Accept-Language")
    return LanguageDetailsV1(
        available_languages=list(available_languages),
        language_tag=language_to_be_delivered.language,
        is_language_fallback=language_to_be_delivered.is_language_fallback,
    )


def select_translation[T](
    translations_by_language: Mapping[Language, T],
    *,
    language: Optional[RequestedLanguageTag],
    accept_language: Optional[str],
    response: Response,
) -> SelectedTranslation[T]:
    """Select the translation to be delivered and describe the selection.

    See `select_language()`. Raises `ValueError` if there are no translations
    at all, so callers have to handle missing content before selecting a
    translation.
    """
    language_details: Final = select_language(
        list(translations_by_language),
        language=language,
        accept_language=accept_language,
        response=response,
    )
    translation: Final = translations_by_language.get(language_details.language_tag)
    if translation is None:
        # This should never happen because the language to be delivered is always one of the available ones.
        raise RuntimeError("Selected language is not among the available translations.")
    return SelectedTranslation(translation=translation, language_details=language_details)
