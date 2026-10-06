"""BCP 47 language tags and the display language.

The display language selects which translated content is delivered. It is
independent of the user’s locale, which only affects the formatting of
values such as numbers and dates (see `backend.user_preferences`).

All langcodes functionality that parses tags or creates `Language` objects
must be used through this module, which bounds the memory langcodes uses for
client-provided tags. Elsewhere, `Language` objects returned by this module
are only compared, hashed, and converted with `to_tag()`.
"""

import threading
from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import Protocol
from typing import final
from typing import runtime_checkable

from langcodes import Language
from langcodes import standardize_tag
from langcodes import tag_is_valid
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
# synchronous route function, which FastAPI runs in a thread pool).
_LANGCODES_LOCK = threading.Lock()


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


def _is_valid_bcp_47_tag(value: str) -> bool:
    # Must be called while using langcodes exclusively.

    # Checked before parsing, so overlong tags never reach the caches.
    if len(value) > _MAX_TAG_LENGTH:
        return False
    # langcodes also accepts POSIX-style underscores as a convenience, while
    # browser APIs require BCP 47’s hyphen-separated representation.
    if "_" in value:
        return False
    # `tag_is_valid()` returns `False` for tags that cannot be parsed instead of raising.
    return tag_is_valid(value)


def is_valid_bcp_47_tag(value: str) -> bool:
    """Check whether `value` is a browser-style BCP 47 language tag of at most
    `_MAX_TAG_LENGTH` characters whose subtags are all registered.
    """
    with _using_langcodes():
        return _is_valid_bcp_47_tag(value)


def parse_language(value: str) -> Language:
    """Validate a BCP 47 language tag and parse it into a normalized `Language`
    (casing, deprecated subtags), so its tag may differ in spelling from the input.

    The normalized tag must be valid as well.
    """
    with _using_langcodes():
        if not _is_valid_bcp_47_tag(value):
            raise ValueError("Language must be a valid BCP 47 language tag.")
        language: Final = Language.get(value)
        # The normalized tag is validated again whenever the `Language` is validated, stored, or loaded, so it has to
        # be valid as well. Normalizing may lengthen a tag (`sh` -> `sr-Latn`) or turn a tag that langcodes accepts into
        # one it rejects (`zh-yue-419-Hant` -> `yue-419-Hant`).
        if not _is_valid_bcp_47_tag(language.to_tag()):
            raise ValueError("Language must be a valid BCP 47 language tag.")
    return language


def standardize_language_tag(value: str) -> str:
    """Return the canonical form of a valid BCP 47 language tag (casing,
    redundant script subtags, deprecated subtag replacements).
    """
    with _using_langcodes():
        return standardize_tag(value)


@final
class WrittenLanguage(NamedTuple):
    """A language together with the script it is written in, e.g. `zh` in `Hant` for `zh-TW`."""

    language: str
    script: Optional[str]


def written_language(language: Language) -> Optional[WrittenLanguage]:
    """Determine the language and the (likely) script of `language`, so that
    tags of the same written language can be matched regardless of their
    region or variants (`de-AT` and `de-DE`), while tags in different scripts
    are kept apart (`zh-TW` and `zh-Hans`).

    Returns `None` for tags without a language, such as `und`.
    """
    if language.language is None:
        return None
    with _using_langcodes():
        # Likely subtags are taken from the CLDR, e.g. `zh-TW` -> `zh-Hant-TW`.
        maximized: Final = language.maximize()
    return WrittenLanguage(language=language.language, script=maximized.script)


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
