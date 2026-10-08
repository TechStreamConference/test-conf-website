"""BCP 47 language tags and the display language.

The display language selects which translated content is delivered. It is
independent of the user’s locale, which only affects the formatting of
values such as numbers and dates (see `backend.user_preferences`).

All langcodes functionality that parses tags or creates `Language` objects
must be used through this module, which bounds the memory langcodes uses for
client-provided tags. Elsewhere, `Language` objects returned by this module
are only compared, hashed, converted with `to_tag()`, and their subtags read.
"""

import itertools
import re
import threading
from collections.abc import Generator
from collections.abc import Mapping
from contextlib import contextmanager
from typing import Annotated
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import Protocol
from typing import final
from typing import runtime_checkable

from langcodes import Language
from langcodes.tag_parser import LanguageTagError
from pydantic import AfterValidator
from pydantic import PlainSerializer
from pydantic import PlainValidator

# langcodes caches every tag it has parsed and every `Language` it has created, without any limit. Tags come from
# clients (query parameters, `Accept-Language`), so unlimited caches would let any client grow the memory of the process
# at will: bounding the input per request does not help, since every request may send other tags (e.g. with private-use
# subtags). The caches are therefore cleared once they exceed a maximum number of entries, and tags longer than a
# maximum length are rejected, which bounds the size of each entry. The caches are private, so they are accessed
# defensively: if langcodes stops providing them, nothing is limited and the corresponding test fails instead of the
# requests.
_LANGCODES_CACHE_NAMES = ("_PARSE_CACHE", "_INSTANCES")
_MAX_LANGCODES_CACHE_SIZE = 10_000
# RFC 5646 recommends supporting tags of at least 35 characters, more leaves room for extensions and private use.
_MAX_TAG_LENGTH = 64

# langcodes reads a cache entry right after checking for it, so clearing a cache while another thread uses langcodes
# could fail that thread. The lock keeps this safe even if langcodes is used outside the event loop thread (e.g. by a
# synchronous route function, which FastAPI runs in a thread pool). It is held only briefly, for parsing tags of limited
# length, so it hardly ever blocks the event loop. It is reentrant, so that a function using langcodes exclusively may
# call another one, e.g. `parse_language()`.
_LANGCODES_LOCK = threading.RLock()


@runtime_checkable
class _Cache(Protocol):
    def __len__(self) -> int: ...

    def clear(self) -> None: ...


@contextmanager
def _using_langcodes() -> Generator[None]:
    """Use langcodes exclusively and limit its caches afterward."""
    with _LANGCODES_LOCK:
        try:
            yield
        finally:
            # `Language` objects are compared and hashed by their tag, so dropping the cached ones only costs parsing
            # again.
            for name in _LANGCODES_CACHE_NAMES:
                cache: object = getattr(Language, name, None)
                if isinstance(cache, _Cache) and len(cache) > _MAX_LANGCODES_CACHE_SIZE:
                    cache.clear()


# Browsers only accept tags that are structurally valid according to ECMA-402 (`IsStructurallyValidLanguageTag`),
# i.e. Unicode BCP 47 locale identifiers (UTS #35) without their backwards compatibility syntax. langcodes is more
# lenient: it also accepts POSIX-style underscores, grandfathered tags (`i-klingon`, `en-GB-oed`), extended language
# subtags (`zh-yue`), `root`, and tags consisting of private-use subtags only (`x-foo`), all of which make `Intl` APIs
# throw.
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
                )
            )
            if _has_duplicates(_variants(transformed_language_id)):
                return False
    return True


def _parse_language(value: str) -> Language:
    # Must be called while using langcodes exclusively.

    # Checked before parsing, so overlong or malformed tags never reach the caches.
    if len(value) > _MAX_TAG_LENGTH or not _is_structurally_valid(value):
        raise ValueError("Language must be a valid BCP 47 language tag.")
    try:
        language: Final = Language.get(value)
    except LanguageTagError as error:
        raise ValueError("Language must be a valid BCP 47 language tag.") from error
    # The normalized tag is validated again whenever the `Language` is validated, stored, or loaded, so it has to be
    # valid as well. Normalizing may lengthen a tag (`sh` -> `sr-Latn`). Whether all subtags are registered is
    # checked on the `Language` rather than on its tag, which would add another entry to the caches if it differs from
    # the input.
    normalized_tag: Final = language.to_tag()
    if len(normalized_tag) > _MAX_TAG_LENGTH or not _is_structurally_valid(normalized_tag) or not language.is_valid():
        raise ValueError("Language must be a valid BCP 47 language tag.")
    return language


def is_valid_bcp_47_tag(value: str) -> bool:
    """Check whether `value` is a BCP 47 language tag of at most
    `_MAX_TAG_LENGTH` characters that browsers accept and whose subtags are all
    registered, and whose normalized form is valid as well (see
    `parse_language()`).
    """
    with _using_langcodes():
        try:
            _ = _parse_language(value)
        except ValueError:
            return False
    return True


def parse_language(value: str) -> Language:
    """Validate a BCP 47 language tag and parse it into a normalized `Language`
    (casing, deprecated subtags), so its tag may differ in spelling from the input.

    The normalized tag must be valid as well.
    """
    with _using_langcodes():
        return _parse_language(value)


def normalize_language_tag(value: str) -> str | None:
    """Return the tag of the normalized `Language` of `value` (see
    `parse_language()`), in which content languages are stored, or `None` if
    `value` is not a valid BCP 47 language tag.
    """
    try:
        return parse_language(value).to_tag()
    except ValueError:
        return None


# The language that content falls back to if the requested language is not available.
ENGLISH = parse_language("en")


@final
class ContentSelection[T](NamedTuple):
    """Content selected by `select_content_language()`."""

    content: T
    is_language_fallback: bool
    """Whether the content is not in the requested language."""


def select_content_language[T](contents_by_language_tag: Mapping[str, T], language_tag: str) -> ContentSelection[T]:
    """Select the content in the requested language. If it is not available,
    fall back to English, or, if that is not available either, to the first
    content.

    Both the requested and the stored tags are compared in their normalized
    form (see `normalize_language_tag()`), so content is found regardless of
    how either tag is spelled (`DE` and `de`, `iw` and `he`). Content stored
    with an invalid tag is only ever selected as the first content, and of
    several contents whose tags normalize to the same tag, the first one is
    selected.

    Raises `ValueError` if there is no content at all.
    """
    if not contents_by_language_tag:
        raise ValueError("There must be content in at least one language.")
    contents_by_normalized_tag: Final[dict[str, T]] = {}
    for stored_tag, content in contents_by_language_tag.items():
        normalized_tag = normalize_language_tag(stored_tag)
        if normalized_tag is not None:
            _ = contents_by_normalized_tag.setdefault(normalized_tag, content)

    requested_tag: Final = normalize_language_tag(language_tag)
    if requested_tag is not None and requested_tag in contents_by_normalized_tag:
        return ContentSelection(contents_by_normalized_tag[requested_tag], is_language_fallback=False)
    if (english_tag := ENGLISH.to_tag()) in contents_by_normalized_tag:
        return ContentSelection(contents_by_normalized_tag[english_tag], is_language_fallback=True)
    return ContentSelection(next(iter(contents_by_language_tag.values())), is_language_fallback=True)


def standardize_language_tag(value: str) -> str:
    """Return the canonical form of a valid BCP 47 language tag (casing,
    redundant script subtags, deprecated subtag replacements).

    Raises `ValueError` for tags that are not valid (see `is_valid_bcp_47_tag()`).
    """
    with _using_langcodes():
        # Validated like every other tag before standardizing it, so that overlong tags never reach the caches and the
        # canonical form, which is never longer than the normalized one, stays within the length limit. Standardized
        # like `langcodes.standardize_tag()` does.
        return _parse_language(value).simplify_script().to_tag()


# Different languages that CLDR's language matching treats as the same language (with a distance smaller than between
# regions of the same language), mapped to one of them: Norwegian (`no`) is written as Norwegian Bokmål (`nb`) by far
# most of the time, unlike Norwegian Nynorsk (`nn`). A test checks this against the matching data of langcodes.
_EQUIVALENT_LANGUAGES = {"no": "nb"}


@final
class WrittenLanguage(NamedTuple):
    """A language together with the script it is written in, e.g. `zh` in `Hant` for `zh-TW`."""

    language: str
    """The language subtag, where languages that are matched as the same language share one of their subtags."""
    script: Optional[str]


# Language subtags that do not name a particular language: uncoded languages (`mis`), multiple languages (`mul`), and no
# linguistic content (`zxx`). An undetermined language (`und`) is parsed as no language at all.
_SPECIAL_LANGUAGES = frozenset({"mis", "mul", "zxx"})
# Subtags reserved for private use (RFC 5646, sections 2.2.1 and 2.2.3) only have a meaning that the parties exchanging
# them agreed on, just like private-use subtags after `x-`.
_PRIVATE_USE_LANGUAGES = ("qaa", "qtz")
_PRIVATE_USE_SCRIPTS = ("qaaa", "qabx")
_UNKNOWN_SCRIPT = "zzzz"


def _is_in_range(subtag: str, bounds: tuple[str, str]) -> bool:
    first, last = bounds
    return len(subtag) == len(first) and first <= subtag.lower() <= last


def _names_no_particular_language(language: str) -> bool:
    # langcodes stores the subtags of a tag that consists of private-use subtags only (`x-foo`) as its language, unlike
    # those of a tag that has a language subtag before them (`und-x-foo`).
    return (
        language.startswith("x-")
        or language.lower() in _SPECIAL_LANGUAGES
        or _is_in_range(language, _PRIVATE_USE_LANGUAGES)
    )


def _names_no_particular_script(script: str) -> bool:
    return script.lower() == _UNKNOWN_SCRIPT or _is_in_range(script, _PRIVATE_USE_SCRIPTS)


def written_language(language: Language) -> WrittenLanguage | None:
    """Determine the language and the (likely) script of `language`, so that
    tags of the same written language can be matched regardless of their
    region or variants (`de-AT` and `de-DE`), while tags in different scripts
    are kept apart (`zh-TW` and `zh-Hans`).

    Like in CLDR's language matching, an individual language is the same as
    its macrolanguage if it is the dominant one (`cmn` and `zh`), and
    Norwegian is the same as Norwegian Bokmål (`no` and `nb`).

    Returns `None` for tags that do not name a particular language: tags
    without a language (`und`), private-use languages (`qaa` to `qtz`, or a
    private-use tag such as `x-foo`), and the special languages `mis`, `mul`,
    and `zxx`. Likewise, a private-use (`Qaaa` to `Qabx`) or unknown (`Zzzz`)
    script is replaced with the likely script of the language.
    """
    if language.language is None or _names_no_particular_language(language.language):
        return None
    with _using_langcodes():
        # Likely scripts only depend on the language and the region.
        with_known_script: Final = (
            Language.make(language=language.language, territory=language.territory)
            if language.script is not None and _names_no_particular_script(language.script)
            else language
        )
        # Likely subtags are taken from the CLDR, e.g. `zh-TW` -> `zh-Hant-TW`.
        maximized: Final = with_known_script.prefer_macrolanguage().maximize()
    # Neither replacing a language with its macrolanguage nor maximizing removes the language.
    matched_language: Final = maximized.language or language.language
    return WrittenLanguage(
        language=_EQUIVALENT_LANGUAGES.get(matched_language, matched_language),
        script=maximized.script,
    )


def _validate_language(value: object) -> Language:
    # A `Language` may have been created without validation or normalization (e.g. by `Language.make()`), so its tag is
    # validated like any other.
    if isinstance(value, Language):
        return parse_language(value.to_tag())
    if isinstance(value, str):
        return parse_language(value)
    raise ValueError("Language must be a valid BCP 47 language tag.")


def _serialize_language(value: Language) -> str:
    return value.to_tag()


# Pydantic cannot build a schema for `Language` itself, so a plain validator replaces the inner validation
# entirely. Both the input and the serialized output are BCP 47 strings in the OpenAPI document.
type Bcp47Language = Annotated[
    Language,
    PlainValidator(_validate_language, json_schema_input_type=str),
    PlainSerializer(_serialize_language, return_type=str),
]


def _validate_language_tag(value: str) -> str:
    # Parsed rather than only checked, since the tag is parsed later on and its normalized form has to be valid as well.
    _ = parse_language(value)
    return value


# Validated like `Bcp47Language`, but kept in its original spelling for clients that look the tag up in their own list.
type Bcp47LanguageTag = Annotated[str, AfterValidator(_validate_language_tag)]


def validate_locale(value: str) -> str:
    """Validate a browser-style BCP 47 language tag without canonicalizing it."""
    if not is_valid_bcp_47_tag(value):
        raise ValueError("Locale must be a valid BCP 47 language tag.")
    return value


# The locale of a user, which only affects the formatting of values, in its original spelling. It is validated just like
# `Bcp47LanguageTag`, but deliberately a separate type: a language tag selects the language that content is delivered
# in, while a locale only selects how values such as dates are formatted, and both are chosen independently.
type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
