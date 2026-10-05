from typing import Final
from typing import final
from typing import override

from langcodes import Language
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator
from sqlmodel.sql.sqltypes import AutoString

from backend.language_tags import parse_language


@final
class LanguageTagType(TypeDecorator[Language]):
    """Stores a display `Language` as its BCP 47 tag.

    The database column stays a plain string, so using this type requires no
    schema change. Languages are written in their normalized spelling
    (`Language.to_tag()`), so stored tags must be normalized as well for SQL
    comparisons to match (migration `33bb3322c275` normalized the existing
    ones). Stored tags are parsed when loaded; an invalid tag fails loudly
    instead of being passed on.
    """

    impl = AutoString
    cache_ok = True

    @override
    def process_bind_param(self, value: object, dialect: Dialect) -> str | None:
        if value is None:
            return None
        # Guard against plain strings, which would bypass the normalization.
        if not isinstance(value, Language):
            message: Final = f"Expected a `Language`, got `{type(value).__name__}`."
            raise TypeError(message)
        return value.to_tag()

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> Language | None:
        return None if value is None else parse_language(value)
