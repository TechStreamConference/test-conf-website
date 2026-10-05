"""BCP 47 language tags and the display language.

The display language selects which translated content is delivered. It is
independent of the user’s locale, which only affects the formatting of
values such as numbers and dates (see `backend.user_preferences`).
"""

from typing import Annotated

from langcodes import Language
from langcodes import tag_is_valid
from pydantic import PlainSerializer
from pydantic import PlainValidator


def is_valid_bcp_47_tag(value: str) -> bool:
    """Check whether `value` is a browser-style BCP 47 language tag whose
    subtags are all registered.
    """
    # langcodes also accepts POSIX-style underscores as a convenience, while
    # browser APIs require BCP 47’s hyphen-separated representation.
    if "_" in value:
        return False
    # `tag_is_valid()` returns `False` for tags that cannot be parsed instead of raising.
    return tag_is_valid(value)


def parse_language(value: str) -> Language:
    """Validate a BCP 47 language tag and parse it into a normalized `Language`
    (casing, deprecated subtags), so its tag may differ in spelling from the input.
    """
    if not is_valid_bcp_47_tag(value):
        raise ValueError("Language must be a valid BCP 47 language tag.")
    return Language.get(value)


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
