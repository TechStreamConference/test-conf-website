from collections.abc import Callable
from typing import Final
from typing import final
from typing import override

from langcodes import Language
from sqlalchemy.engine import Dialect
from sqlalchemy.types import TypeDecorator
from sqlmodel.sql.sqltypes import AutoString

from backend.language_tags import parse_language


def _language_sort_key(language: Language) -> str:
    return language.to_tag()


@final
class LanguageTagType(TypeDecorator[Language]):
    """Stores a display `Language` as its BCP 47 tag.

    The database column stays a plain string, so using this type requires no
    schema change. Languages are written in their normalized spelling
    (`Language.to_tag()`), so stored tags must be normalized as well for SQL
    comparisons to match (migration `33bb3322c275` normalized the existing
    ones, so a langcodes upgrade that changes the normalization requires
    another such migration). Stored tags are parsed when loaded; an invalid tag fails loudly
    instead of being passed on.
    """

    impl = AutoString
    cache_ok = True

    @property
    @override
    def sort_key_function(self) -> Callable[[Language], str]:
        # The unit of work sorts rows by their primary key before flushing several updates or deletes at once, but
        # `Language` objects are not orderable.
        return _language_sort_key

    @override
    def process_bind_param(self, value: object, dialect: Dialect) -> str | None:
        if value is None:
            return None
        # Guard against plain strings, which would bypass the normalization.
        if not isinstance(value, Language):
            message: Final = f"Expected a `Language`, got `{type(value).__name__}`."
            raise TypeError(message)
        # Table models are not validated, so the `Language` may have been created without validation or normalization
        # (e.g. by `Language.make()`). Storing a tag that cannot be loaded again must fail right away.
        return parse_language(value.to_tag()).to_tag()

    @override
    def process_result_value(self, value: str | None, dialect: Dialect) -> Language | None:
        return None if value is None else parse_language(value)
