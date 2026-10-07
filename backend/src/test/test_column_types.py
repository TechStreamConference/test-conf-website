import json
from collections.abc import Iterator
from importlib.resources import files
from pathlib import Path
from typing import Final
from typing import Optional

import pytest
import sqlalchemy as sa
from langcodes import Language
from sqlalchemy.dialects import postgresql
from sqlmodel import col
from sqlmodel import select

from backend.language_tags import parse_language
from backend.models.column_types import LanguageTagType
from backend.models.tables import EventTranslation
from backend.models.tables import StaticPage

_TYPE = LanguageTagType()
_DIALECT = postgresql.dialect()
_NORMALIZATION_SNAPSHOT_PATH = Path(__file__).with_name("language_tag_normalization.json")


def test_language_is_stored_as_its_normalized_tag() -> None:
    assert _TYPE.process_bind_param(Language.get("en-us"), _DIALECT) == "en-US"


def test_unnormalized_language_is_stored_as_its_normalized_tag() -> None:
    assert _TYPE.process_bind_param(Language.make(language="iw"), _DIALECT) == "he"


@pytest.mark.parametrize(
    "language",
    [Language.make(language="xx"), Language.make(language="de", private="x-" + "-".join(["abcdefgh"] * 7))],
    ids=["unregistered", "overlong"],
)
def test_invalid_languages_are_rejected_when_storing(language: Language) -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = _TYPE.process_bind_param(language, _DIALECT)


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


def _registered_tags() -> Iterator[str]:
    """Yield a tag for each record of the IANA language subtag registry that langcodes bundles."""
    registry: Final = files("langcodes").joinpath("data", "language-subtag-registry.txt").read_text(encoding="utf-8")
    # The first record only holds the date of the registry.
    for record in registry.split("\n%%\n")[1:]:
        fields: dict[str, str] = {}
        for line in record.splitlines():
            # Indented lines only continue descriptions and comments. Of several prefixes, the first one is used.
            if not line.startswith(" "):
                name, _, value = line.partition(": ")
                _ = fields.setdefault(name, value)
        subtag = fields.get("Subtag", "")
        # Ranges of private-use subtags (`qaa..qtz`) have no registered meaning that could be normalized.
        if ".." in subtag:
            continue
        match fields["Type"]:
            case "language":
                yield subtag
            case "extlang" | "variant":
                yield f"{fields.get('Prefix', 'und')}-{subtag}"
            case "script" | "region":
                yield f"und-{subtag}"
            case _:
                # Grandfathered and redundant tags are registered as a whole.
                yield fields["Tag"]


def _normalize(tag: str) -> Optional[str]:
    try:
        return parse_language(tag).to_tag()
    except ValueError:
        return None


# Stored tags are only found and loaded as the languages they were stored as if langcodes still normalizes them the same
# way (see `LanguageTagType`). Normalization replaces deprecated subtags based on the registry, so a langcodes upgrade
# may change it without any error. The snapshot pins every registered tag that is not kept as is, mapped to its
# normalized tag, or to `null` if it is rejected.
def test_registered_tags_are_normalized_like_when_stored() -> None:
    snapshot: Final = json.loads(_NORMALIZATION_SNAPSHOT_PATH.read_text(encoding="utf-8"))

    changed_tags: Final = {tag: normalized for tag in _registered_tags() if (normalized := _normalize(tag)) != tag}

    assert changed_tags == snapshot, (
        "langcodes normalizes registered tags differently than when the stored tags were normalized. Add a "
        + "migration that normalizes the stored tags again (like `33bb3322c275`), then update "
        + f"`{_NORMALIZATION_SNAPSHOT_PATH.name}`."
    )
