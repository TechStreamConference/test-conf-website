from collections.abc import Sized
from typing import Final
from typing import Literal
from typing import Optional

import pytest
from langcodes import Language
from pydantic import TypeAdapter
from pydantic import ValidationError

import backend.language_tags
from backend.language_tags import Bcp47Language
from backend.language_tags import Bcp47LanguageTag
from backend.language_tags import is_valid_bcp_47_tag
from backend.language_tags import parse_language

_ADAPTER = TypeAdapter[Bcp47Language](Bcp47Language)


@pytest.mark.parametrize("tag", ["de", "de-DE", "zh-Hant-TW", "haw", "en-US-x-private", "i-klingon"])
def test_registered_tags_are_valid(tag: str) -> None:
    assert is_valid_bcp_47_tag(tag)


@pytest.mark.parametrize("tag", ["", "en_US", "en--US", "en-", "not a tag", "abc-123", "123", "x", "dé"])
def test_malformed_or_unregistered_tags_are_invalid(tag: str) -> None:
    assert not is_valid_bcp_47_tag(tag)


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


def test_bcp_47_language_parses_strings_into_languages() -> None:
    validated: Final = _ADAPTER.validate_python("de-de")

    assert isinstance(validated, Language)
    assert validated == Language.get("de-DE")


def test_bcp_47_language_accepts_languages_unchanged() -> None:
    language: Final = Language.get("en-US")

    assert _ADAPTER.validate_python(language) is language


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


@pytest.mark.parametrize("value", ["en_US", "abc-123", ""])
def test_bcp_47_language_tag_rejects_invalid_tags(value: str) -> None:
    with pytest.raises(ValidationError):
        _ = _TAG_ADAPTER.validate_python(value)
