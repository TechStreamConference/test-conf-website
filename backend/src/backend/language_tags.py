"""BCP 47 language tags and the display language.

The display language selects which translated content is delivered. It is
independent of the user’s locale, which only affects the formatting of
values such as numbers and dates (see `backend.user_preferences`).
"""

from typing import Annotated
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import Protocol
from typing import final
from typing import runtime_checkable

from langcodes import Language
from langcodes import tag_is_valid
from pydantic import AfterValidator
from pydantic import PlainSerializer
from pydantic import PlainValidator

# langcodes caches every tag it has parsed and every `Language` it has created, without any limit. Tags come from
# clients (query parameters, `Accept-Language`), so unlimited caches would let any client grow the memory of the process
# at will. The caches are private, so they are accessed defensively: if langcodes stops providing them, nothing is
# limited and the corresponding test fails instead of the requests.
_LANGCODES_CACHE_NAMES = ("_PARSE_CACHE", "_INSTANCES")
_MAX_LANGCODES_CACHE_SIZE = 10_000


@runtime_checkable
class _Cache(Protocol):
    def __len__(self) -> int: ...

    def clear(self) -> None: ...


def _limit_langcodes_caches() -> None:
    # `Language` objects are compared and hashed by their tag, so dropping the cached ones only costs parsing again.
    # Clearing is only safe because langcodes is never used outside the event loop thread: langcodes reads a cache
    # entry right after checking for it.
    for name in _LANGCODES_CACHE_NAMES:
        cache: object = getattr(Language, name, None)
        if isinstance(cache, _Cache) and len(cache) > _MAX_LANGCODES_CACHE_SIZE:
            cache.clear()


def is_valid_bcp_47_tag(value: str) -> bool:
    """Check whether `value` is a browser-style BCP 47 language tag whose
    subtags are all registered.
    """
    # langcodes also accepts POSIX-style underscores as a convenience, while
    # browser APIs require BCP 47’s hyphen-separated representation.
    if "_" in value:
        return False
    # `tag_is_valid()` returns `False` for tags that cannot be parsed instead of raising.
    valid: Final = tag_is_valid(value)
    # Every client-provided tag is validated here before it is parsed, so this covers all of them.
    _limit_langcodes_caches()
    return valid


def parse_language(value: str) -> Language:
    """Validate a BCP 47 language tag and parse it into a normalized `Language`
    (casing, deprecated subtags), so its tag may differ in spelling from the input.
    """
    if not is_valid_bcp_47_tag(value):
        raise ValueError("Language must be a valid BCP 47 language tag.")
    return Language.get(value)


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
    # Likely subtags are taken from the CLDR, e.g. `zh-TW` -> `zh-Hant-TW`.
    maximized: Final = language.maximize()
    _limit_langcodes_caches()
    return WrittenLanguage(language=language.language, script=maximized.script)


def _validate_language(value: object) -> Language:
    if isinstance(value, Language):
        return value
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
    if not is_valid_bcp_47_tag(value):
        raise ValueError("Language must be a valid BCP 47 language tag.")
    return value


# Validated like `Bcp47Language`, but kept in its original spelling for clients that look the tag up in their own list.
type Bcp47LanguageTag = Annotated[str, AfterValidator(_validate_language_tag)]
