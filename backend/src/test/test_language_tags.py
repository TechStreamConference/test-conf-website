import ast
import threading
from collections.abc import Iterator
from collections.abc import Sized
from pathlib import Path
from typing import Final
from typing import Literal
from typing import Optional

import pytest
from langcodes import Language
from langcodes.data_dicts import LANGUAGE_DISTANCES
from langcodes.language_distance import DEFAULT_TERRITORY_DISTANCE
from pydantic import TypeAdapter
from pydantic import ValidationError

import backend
import backend.language_tags
from backend.language_tags import Bcp47Language
from backend.language_tags import Bcp47LanguageTag
from backend.language_tags import is_valid_bcp_47_tag
from backend.language_tags import parse_language
from backend.language_tags import written_language

_ADAPTER = TypeAdapter[Bcp47Language](Bcp47Language)


@pytest.mark.parametrize("tag", ["de", "de-DE", "zh-Hant-TW", "haw", "en-US-x-private", "i-klingon"])
def test_registered_tags_are_valid(tag: str) -> None:
    assert is_valid_bcp_47_tag(tag)


@pytest.mark.parametrize("tag", ["", "en_US", "en--US", "en-", "not a tag", "abc-123", "123", "x", "dé"])
def test_malformed_or_unregistered_tags_are_invalid(tag: str) -> None:
    assert not is_valid_bcp_47_tag(tag)


def test_overlong_tags_are_invalid() -> None:
    private_use: Final = "en-x-" + "-".join(["abcdefgh"] * 7)

    assert len(private_use) == 67
    assert not is_valid_bcp_47_tag(private_use)
    assert is_valid_bcp_47_tag(private_use[:64].rstrip("-"))


def test_langcodes_is_used_exclusively(monkeypatch: pytest.MonkeyPatch) -> None:
    lock: Final = threading.Lock()
    monkeypatch.setattr(backend.language_tags, "_LANGCODES_LOCK", lock)

    def _tag_is_valid(_tag: str) -> bool:
        assert lock.locked()
        return True

    monkeypatch.setattr(backend.language_tags, "tag_is_valid", _tag_is_valid)

    assert is_valid_bcp_47_tag("de")
    assert not lock.locked()


def _langcodes_uses_outside_language_tags() -> Iterator[str]:
    backend_dir: Final = Path(backend.__file__).parent
    for path in sorted(backend_dir.rglob("*.py")):
        if path == Path(backend.language_tags.__file__):
            continue
        location = path.relative_to(backend_dir)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import) and any(alias.name.startswith("langcodes") for alias in node.names):
                yield f"{location}: imports `langcodes`"
            elif isinstance(node, ast.ImportFrom) and node.module == "langcodes":
                yield from (f"{location}: imports `{alias.name}`" for alias in node.names if alias.name != "Language")
            elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id == "Language":
                yield f"{location}: uses `Language.{node.attr}`"


# The caches are only limited safely if every use of langcodes that may fill them goes through `backend.language_tags`.
def test_langcodes_is_only_used_through_language_tags() -> None:
    assert list(_langcodes_uses_outside_language_tags()) == []


@pytest.mark.parametrize("cache_name", ["_PARSE_CACHE", "_INSTANCES"])
def test_langcodes_caches_are_limited(monkeypatch: pytest.MonkeyPatch, cache_name: str) -> None:
    monkeypatch.setattr(backend.language_tags, "_MAX_LANGCODES_CACHE_SIZE", 10)
    german: Final = parse_language("de")

    # Clients can send any number of distinct tags, e.g. with private-use subtags.
    for i in range(100):
        assert is_valid_bcp_47_tag(f"en-x-tag{i:04}")

    cache: Final[object] = getattr(Language, cache_name, None)
    assert isinstance(cache, Sized), f"langcodes no longer provides `Language.{cache_name}`"
    assert len(cache) <= 10
    # Dropped `Language` objects are still equal to newly parsed ones.
    assert parse_language("de") == german


@pytest.mark.parametrize(
    ("tag", "normalized"),
    [
        ("de", "de"),
        ("en-us", "en-US"),
        ("ZH-hant-tw", "zh-Hant-TW"),
        # Deprecated language subtag.
        ("iw", "he"),
    ],
)
def test_parse_language_normalizes_the_tag(tag: str, normalized: str) -> None:
    assert parse_language(tag).to_tag() == normalized


def test_parse_language_rejects_invalid_tags() -> None:
    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = parse_language("en_US")


# Normalized to `sr-Latn-x-…`, which exceeds the length limit although the tag itself does not.
_LENGTHENED_BY_NORMALIZATION = "sh-x-" + "-".join(["abcdefgh"] * 6) + "-abcde"


def test_parse_language_rejects_tags_whose_normalized_form_is_overlong() -> None:
    assert len(_LENGTHENED_BY_NORMALIZATION) == 64
    assert is_valid_bcp_47_tag(_LENGTHENED_BY_NORMALIZATION)

    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = parse_language(_LENGTHENED_BY_NORMALIZATION)


# Normalized to `yue-419-Hant`, which langcodes rejects although it accepts the tag itself.
_INVALIDATED_BY_NORMALIZATION = "zh-yue-419-Hant"


def test_parse_language_rejects_tags_whose_normalized_form_is_invalid() -> None:
    assert is_valid_bcp_47_tag(_INVALIDATED_BY_NORMALIZATION)

    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = parse_language(_INVALIDATED_BY_NORMALIZATION)


def test_parse_language_accepts_lengthened_tags_within_the_limit() -> None:
    tag: Final = _LENGTHENED_BY_NORMALIZATION.removesuffix("-abcde")

    assert parse_language(tag).to_tag() == "sr-Latn" + tag.removeprefix("sh")


def test_bcp_47_language_parses_strings_into_languages() -> None:
    validated: Final = _ADAPTER.validate_python("de-de")

    assert isinstance(validated, Language)
    assert validated == Language.get("de-DE")


def test_bcp_47_language_accepts_valid_languages() -> None:
    assert _ADAPTER.validate_python(Language.get("en-US")) == Language.get("en-US")


def test_bcp_47_language_normalizes_unnormalized_languages() -> None:
    assert _ADAPTER.validate_python(Language.make(language="iw")) == Language.get("he")


@pytest.mark.parametrize(
    "language",
    [Language.make(language="xx"), Language.make(language="de", private="x-" + "-".join(["abcdefgh"] * 7))],
    ids=["unregistered", "overlong"],
)
def test_bcp_47_language_rejects_invalid_languages(language: Language) -> None:
    with pytest.raises(ValidationError, match="BCP 47"):
        _ = _ADAPTER.validate_python(language)


@pytest.mark.parametrize("value", ["en_US", "abc-123", "", 42, None])
def test_bcp_47_language_rejects_invalid_values(value: object) -> None:
    with pytest.raises(ValidationError, match="BCP 47"):
        _ = _ADAPTER.validate_python(value)


def test_bcp_47_language_parses_json_strings() -> None:
    assert _ADAPTER.validate_json('"zh-Hant-TW"') == Language.get("zh-Hant-TW")


@pytest.mark.parametrize("mode", ["python", "json"])
def test_bcp_47_language_serializes_to_its_tag(mode: Literal["python", "json"]) -> None:
    assert _ADAPTER.dump_python(Language.get("en-us"), mode=mode) == "en-US"


def test_bcp_47_language_round_trips_through_json() -> None:
    language: Final = Language.get("sr-Latn-RS")

    assert _ADAPTER.validate_json(_ADAPTER.dump_json(language)) == language


@pytest.mark.parametrize("mode", ["validation", "serialization"])
def test_bcp_47_language_is_a_string_in_the_json_schema(mode: Literal["validation", "serialization"]) -> None:
    # The generated frontend client must keep seeing a plain string.
    assert _ADAPTER.json_schema(mode=mode) == {"type": "string"}


def test_optional_bcp_47_language_accepts_none() -> None:
    assert TypeAdapter[Optional[Bcp47Language]](Optional[Bcp47Language]).validate_python(None) is None


_TAG_ADAPTER = TypeAdapter[Bcp47LanguageTag](Bcp47LanguageTag)


def test_bcp_47_language_tag_keeps_the_original_spelling() -> None:
    assert _TAG_ADAPTER.validate_python("en-us") == "en-us"
    assert _TAG_ADAPTER.validate_python("iw") == "iw"


@pytest.mark.parametrize("value", ["en_US", "abc-123", "", _LENGTHENED_BY_NORMALIZATION, _INVALIDATED_BY_NORMALIZATION])
def test_bcp_47_language_tag_rejects_invalid_tags(value: str) -> None:
    with pytest.raises(ValidationError):
        _ = _TAG_ADAPTER.validate_python(value)


def _closest_different_languages() -> Iterator[tuple[str, str]]:
    """Yield the pairs of different languages that CLDR's language matching
    treats as closer than the same language in different regions.
    """
    # Besides languages, the distances also cover scripts of languages (`sr_Latn`) and wildcards (`*`).
    for desired, distances in LANGUAGE_DISTANCES.items():
        for supported, distance in distances.items():
            if (
                desired.isalpha()
                and supported.isalpha()
                and desired != supported
                and distance < DEFAULT_TERRITORY_DISTANCE
            ):
                yield desired, supported


def test_closest_different_languages_are_the_same_written_language() -> None:
    pairs: Final = list(_closest_different_languages())

    # Keeps the test from passing without checking anything if the matching data of langcodes changes its format.
    assert ("nb", "no") in pairs
    for desired, supported in pairs:
        assert written_language(parse_language(desired)) == written_language(parse_language(supported))


@pytest.mark.parametrize(("tag", "macrolanguage"), [("cmn", "zh"), ("zsm", "ms"), ("arb", "ar")])
def test_dominant_languages_are_the_same_written_language_as_their_macrolanguage(tag: str, macrolanguage: str) -> None:
    assert written_language(parse_language(tag)) == written_language(parse_language(macrolanguage))


@pytest.mark.parametrize(("tag", "other_tag"), [("nn", "nb"), ("nn", "no"), ("yue", "zh-Hant")])
def test_other_languages_are_different_written_languages(tag: str, other_tag: str) -> None:
    assert written_language(parse_language(tag)) != written_language(parse_language(other_tag))


@pytest.mark.parametrize("tag", ["und", "und-DE", "und-x-foo", "x-foo", "x-pig-latin"])
def test_tags_without_a_language_have_no_written_language(tag: str) -> None:
    assert written_language(parse_language(tag)) is None
