"""Selection of the language in which translated content is delivered.

The language is resolved in the following order:

1. the requested language (the `language` query parameter, if given and a
   valid BCP 47 tag),
2. the best available language from the `Accept-Language` header (respecting
   quality values),
3. English,
4. the first available language.

Language tags are matched by their canonical form and fall back to more
general tags as in RFC 4647 lookup (e.g. `de-DE` matches `de`). Only the
requested tags are truncated, never the available ones, so translated content
is stored under plain language subtags (enforced by check constraints in
`backend.models.tables`).

The delivered language is marked as a fallback if the client's first choice
(the requested language or, if not given, the most preferred valid header
entry) is not available. A requested language that is not a valid BCP 47 tag
is handled like an unavailable one rather than failing the request, so a
stale or malformed tag still delivers content. If the client did not express
any preference at all, there is no first choice that could be missing, so
English or the first available language is not marked as a fallback.
"""

from collections.abc import Iterator
from collections.abc import Mapping
from collections.abc import Sequence
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final

from fastapi import Response
from langcodes import Language
from werkzeug.datastructures import LanguageAccept
from werkzeug.http import parse_accept_header

from backend.language_tags import parse_language
from backend.models.responses import LanguageDetailsV1

LANGUAGE_SELECTION_DESCRIPTION = (
    "The language is selected in the following order: the requested language (`language`, if given and a "
    + "valid BCP 47 tag; an invalid tag is handled like an unavailable language), "
    + "the best available language from the `Accept-Language` header (respecting quality values), "
    + "English, and finally the first available language. Language tags are matched by their "
    + "canonical form and fall back to more general tags (e.g. `de-DE` matches `de`). Wildcards and "
    + "languages excluded with `q=0` are ignored, so an excluded language may still be delivered as the "
    + "English or first available language. `isLanguageFallback` is `true` if the client's first choice "
    + "(`language` or, if not given, the most preferred valid `Accept-Language` entry) is not available, and "
    + "`false` if the client did not express any preference."
)

_ENGLISH = Language.get("en")

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


def _lookup_tags(tag: str) -> Iterator[str]:
    """Yield `tag` and its progressively truncated forms, most specific first,
    as used by RFC 4647 lookup (e.g. `sr-Latn-RS` -> `sr-Latn` -> `sr`).

    Subtags are removed from the end; a singleton that would end up last is
    removed along with the subtag following it (e.g. `en-US-x-private` ->
    `en-US`).

    See: https://www.rfc-editor.org/rfc/rfc4647#section-3.4
    """
    subtags: Final = tag.split("-")
    while subtags:
        yield "-".join(subtags)
        del subtags[-1]
        if subtags and len(subtags[-1]) == 1:
            del subtags[-1]


def _find_available_language(language: Language, available_languages: Sequence[Language]) -> Optional[Language]:
    """Return the available language that matches the canonical form of
    `language` itself or, failing that, the most specific of its truncated
    forms (RFC 4647 lookup, e.g. `de-DE` -> `de`).
    """
    # `Language` equality is defined by the tag string, so matching on canonical tags is exact. Returning the
    # available object itself (instead of re-parsing the tag) guarantees that the result is usable as a key into the
    # translations.
    available_by_tag: Final = {available.to_tag(): available for available in available_languages}
    return next(
        (available_by_tag[tag] for tag in _lookup_tags(language.to_tag()) if tag in available_by_tag),
        None,
    )


def _parse_valid_language(tag: str) -> Optional[Language]:
    try:
        return parse_language(tag)
    except ValueError:
        return None


def _parse_accept_language_header(header: str) -> list[Language]:
    """Return the languages of an `Accept-Language` header, most preferred first.

    Wildcards, excluded languages (`q=0`), and entries that are not valid BCP 47
    tags are skipped: the header is controlled by the client and an invalid
    entry must not make the whole request fail. Entries are validated like the
    requested language, so an invalid entry is never the client's first choice.

    Excluded languages are ignored rather than avoided, so the English or first
    available language may still be an excluded one: the content is always
    delivered instead of responding with 406 Not Acceptable.
    """
    languages: Final[list[Language]] = []
    for tag, quality in sorted(
        parse_accept_header(header, LanguageAccept),
        key=lambda entry: entry[1],
        reverse=True,
    ):
        if quality <= 0.0 or tag == "*":
            continue
        language = _parse_valid_language(tag)
        if language is not None:
            languages.append(language)
    return languages


def _determine_language_to_be_delivered(
    *,
    language: Optional[RequestedLanguageTag],
    accept_language_header: Optional[str],
    available_languages: Sequence[Language],
) -> _LanguageToBeDelivered:
    if not available_languages:
        raise ValueError("At least one language must be available.")

    # An invalid tag still expresses a preference, so it is handled like an unavailable language.
    requested_language: Final = None if language is None else _parse_valid_language(language)
    if requested_language is not None:
        available_route_language: Final = _find_available_language(requested_language, available_languages)
        if available_route_language is not None:
            return _LanguageToBeDelivered(
                language=available_route_language,
                is_language_fallback=False,
                varies_with_accept_language=False,
            )

    # TODO: Respect the language preference of logged-in users. Requires
    #       `https://github.com/TechStreamConference/test-conf-website/issues/387` to
    #       be resolved first.

    header_languages: Final = (
        [] if accept_language_header is None else _parse_accept_language_header(accept_language_header)
    )
    for i, header_language in enumerate(header_languages):
        available_header_language = _find_available_language(header_language, available_languages)
        if available_header_language is not None:
            return _LanguageToBeDelivered(
                language=available_header_language,
                is_language_fallback=language is not None or i != 0,
                varies_with_accept_language=True,
            )

    # Without a requested language or a valid header entry, there is no first choice that could be missing.
    client_expressed_preference: Final = language is not None or len(header_languages) > 0
    return _LanguageToBeDelivered(
        language=_ENGLISH if _ENGLISH in available_languages else available_languages[0],
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
