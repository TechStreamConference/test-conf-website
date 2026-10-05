from typing import Final

import pytest
import sqlalchemy as sa
from langcodes import Language
from sqlalchemy.dialects import postgresql
from sqlmodel import col
from sqlmodel import select

from backend.models.column_types import LanguageTagType
from backend.models.tables import EventTranslation
from backend.models.tables import StaticPage

_TYPE = LanguageTagType()
_DIALECT = postgresql.dialect()


def test_language_is_stored_as_its_normalized_tag() -> None:
    assert _TYPE.process_bind_param(Language.get("en-us"), _DIALECT) == "en-US"


def test_plain_strings_are_rejected_when_storing() -> None:
    with pytest.raises(TypeError, match="Expected a `Language`, got `str`"):
        _ = _TYPE.process_bind_param("en-US", _DIALECT)


def test_languages_are_sorted_by_their_normalized_tag() -> None:
    languages: Final = [Language.get("en"), Language.get("de-DE"), Language.get("de")]

    assert sorted(languages, key=_TYPE.sort_key_function) == [
        Language.get("de"),
        Language.get("de-DE"),
        Language.get("en"),
    ]


def test_stored_tags_are_loaded_as_languages() -> None:
    assert _TYPE.process_result_value("de-DE", _DIALECT) == Language.get("de-DE")


def test_invalid_stored_tags_fail_when_loading() -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = _TYPE.process_result_value("en_US", _DIALECT)


def test_null_is_stored_as_null() -> None:
    assert _TYPE.process_bind_param(None, _DIALECT) is None


def test_null_is_loaded_as_none() -> None:
    assert _TYPE.process_result_value(None, _DIALECT) is None


@pytest.mark.parametrize("table", [StaticPage, EventTranslation], ids=lambda table: table.__name__)
def test_display_language_columns_use_the_language_tag_type(table: type[StaticPage | EventTranslation]) -> None:
    assert isinstance(sa.inspect(table).columns["language"].type, LanguageTagType)


def test_queries_compare_against_the_normalized_tag() -> None:
    statement: Final = select(StaticPage).where(col(StaticPage.language) == Language.get("DE-at"))

    compiled: Final = str(statement.compile(dialect=_DIALECT, compile_kwargs={"literal_binds": True}))

    assert "static_pages.language = 'de-AT'" in compiled
