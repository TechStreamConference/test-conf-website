import ast
import functools
import inspect
import sys
import threading
from collections.abc import Callable
from collections.abc import Iterator
from collections.abc import Sized
from pathlib import Path
from typing import Final
from typing import Literal
from typing import Optional
from typing import final

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
from backend.language_tags import Bcp47Locale
from backend.language_tags import is_valid_bcp_47_tag
from backend.language_tags import normalize_language_tag
from backend.language_tags import parse_language
from backend.language_tags import select_content_language
from backend.language_tags import standardize_language_tag
from backend.language_tags import validate_locale
from backend.language_tags import written_language

_ADAPTER = TypeAdapter[Bcp47Language](Bcp47Language)
_TAG_ADAPTER = TypeAdapter[Bcp47LanguageTag](Bcp47LanguageTag)
_LOCALE_ADAPTER = TypeAdapter[Bcp47Locale](Bcp47Locale)


@pytest.mark.parametrize(
    "tag",
    [
        "de",
        "de-DE",
        "zh-Hant-TW",
        "haw",
        "en-US-x-private",
        "de-DE-1996",
        "en-US-u-ca-gregory",
        "en-t-de-1996",
        "EN-us",
    ],
)
def test_registered_tags_are_valid(tag: str) -> None:
    assert is_valid_bcp_47_tag(tag)


@pytest.mark.parametrize("tag", ["", "en_US", "en--US", "en-", "not a tag", "abc-123", "123", "x", "dé"])
def test_malformed_or_unregistered_tags_are_invalid(tag: str) -> None:
    assert not is_valid_bcp_47_tag(tag)


def test_non_ascii_tags_are_invalid() -> None:
    # Starts with KELVIN SIGN, whose lowercase form is `k`, so the tag would be accepted as `kin` otherwise.
    assert not is_valid_bcp_47_tag("\u212ain")


# langcodes accepts all of these, while `Intl` APIs of browsers throw on them.
@pytest.mark.parametrize(
    "tag",
    [
        # Backwards compatibility syntax.
        "root",
        "Latn-DE",
        # Irregular grandfathered tags.
        "i-klingon",
        "en-GB-oed",
        "sgn-BE-FR",
        # Extended language subtags.
        "zh-yue",
        "zh-min-nan",
        # Private-use subtags only.
        "x-foo",
        # Duplicate variants or singletons.
        "de-1996-1996",
        "en-a-bbb-a-ddd",
        "en-t-de-1996-1996",
    ],
)
def test_tags_that_browsers_reject_are_invalid(tag: str) -> None:
    assert not is_valid_bcp_47_tag(tag)


# Only private-use subtags may repeat singletons and other subtags.
def test_private_use_subtags_are_not_checked_for_duplicates() -> None:
    assert is_valid_bcp_47_tag("en-a-bbb-x-a-a-bbb")


def test_overlong_tags_are_invalid() -> None:
    private_use: Final = "en-x-" + "-".join(["abcdefgh"] * 7)

    assert len(private_use) == 67
    assert not is_valid_bcp_47_tag(private_use)
    assert is_valid_bcp_47_tag(private_use[:64].rstrip("-"))


# The methods of langcodes that the module uses which parse tags or create `Language` objects.
_LANGCODES_METHODS = ("get", "make", "is_valid", "simplify_script", "prefer_macrolanguage", "maximize")


@final
class _TrackingLock:
    """A reentrant lock that knows whether it is held, which `threading.RLock`
    only does from Python 3.14 on.
    """

    def __init__(self) -> None:
        self._lock: Final = threading.RLock()
        self._depth = 0

    def __enter__(self) -> None:
        _ = self._lock.acquire()
        self._depth += 1

    def __exit__(self, *_: object) -> None:
        self._depth -= 1
        self._lock.release()

    def locked(self) -> bool:
        return self._depth > 0


def test_langcodes_is_used_exclusively(monkeypatch: pytest.MonkeyPatch) -> None:
    lock: Final = _TrackingLock()
    monkeypatch.setattr(backend.language_tags, "_LANGCODES_LOCK", lock)
    used: Final[set[str]] = set()

    def _guard(name: str, method: Callable[..., object]) -> Callable[..., object]:
        @functools.wraps(method)
        def _guarded(*args: object, **kwargs: object) -> object:
            assert lock.locked(), f"`Language.{name}()` is used without the lock"
            used.add(name)
            return method(*args, **kwargs)

        return _guarded

    for name in _LANGCODES_METHODS:
        # Static and class methods are already bound when accessed through the class, instance methods are not.
        bound = isinstance(inspect.getattr_static(Language, name), staticmethod | classmethod)
        guarded = _guard(name, getattr(Language, name))
        monkeypatch.setattr(Language, name, staticmethod(guarded) if bound else guarded)

    assert is_valid_bcp_47_tag("de-AT")
    assert standardize_language_tag("de-at") == "de-AT"
    # The private-use script is replaced, which creates another `Language`.
    language: Final = parse_language("zh-Qaaa-TW")
    assert written_language(language) == ("zh", "Hant")
    assert _ADAPTER.validate_python(language) == language
    assert _TAG_ADAPTER.validate_python("de-at") == "de-at"

    assert not lock.locked()
    # Keeps the test from passing without checking anything if the module stops using one of the methods.
    assert used == set(_LANGCODES_METHODS)


def test_langcodes_may_be_used_reentrantly() -> None:
    def _use_reentrantly() -> None:
        with backend.language_tags._using_langcodes():  # type: ignore[reportPrivateUsage]
            _ = parse_language("de")

    # Run in another thread, so that a deadlock fails the test instead of hanging it.
    thread: Final = threading.Thread(target=_use_reentrantly, daemon=True)
    thread.start()
    thread.join(timeout=5)

    assert not thread.is_alive()


def _annotations(module: ast.Module) -> Iterator[ast.expr]:
    for node in ast.walk(module):
        if isinstance(node, ast.arg | ast.AnnAssign) and node.annotation is not None:
            yield node.annotation
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.returns is not None:
            yield node.returns
        elif isinstance(node, ast.TypeAlias):
            yield node.value


def _langcodes_uses(module: ast.Module) -> Iterator[str]:
    """Yield the uses of langcodes in `module` other than annotating with `Language`."""
    in_annotations: Final = {id(node) for annotation in _annotations(module) for node in ast.walk(annotation)}
    for node in ast.walk(module):
        if isinstance(node, ast.Import):
            yield from (ast.unparse(alias) for alias in node.names if alias.name.split(".")[0] == "langcodes")
        elif isinstance(node, ast.ImportFrom) and (node.module or "").split(".")[0] == "langcodes":
            # `Language` may only be imported under its own name, so that every use of it is found below.
            yield from (
                ast.unparse(alias)
                for alias in node.names
                if node.module != "langcodes" or alias.name != "Language" or alias.asname is not None
            )
        elif isinstance(node, ast.Name) and node.id == "Language" and id(node) not in in_annotations:
            # Any other use, including passing `Language` on (`getattr(Language, "get")`) or binding it to another name.
            yield f"Language in line {node.lineno}"
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and node.value.split(".")[0] == "langcodes":
            # Dynamic imports (`importlib.import_module("langcodes")`, `sys.modules["langcodes"]`).
            yield repr(node.value)


@pytest.mark.parametrize(
    "source",
    [
        "import langcodes",
        "import langcodes.tag_parser as parser",
        "from langcodes import standardize_tag",
        "from langcodes import Language as Lang",
        "from langcodes.language_distance import tuple_distance_cached",
        "from langcodes import Language\nLanguage.get('de')",
        "from langcodes import Language\nLanguage('de')",
        "from langcodes import Language\ngetattr(Language, 'get')('de')",
        "from langcodes import Language\nLang = Language",
        "from langcodes import Language\nadapter = TypeAdapter[Language](Language)",
        "import importlib\nimportlib.import_module('langcodes')",
        "import sys\nsys.modules['langcodes.tag_parser']",
    ],
)
def test_uses_of_langcodes_are_found(source: str) -> None:
    assert list(_langcodes_uses(ast.parse(source)))


@pytest.mark.parametrize(
    "source",
    [
        "from langcodes import Language\ndef f(language: Language) -> list[Language]: ...",
        "from langcodes import Language\nlanguages: dict[Language, str] = {}",
        "from langcodes import Language\ntype Languages = list[Language]",
        "from langcodes import Language\nclass C:\n    language: Language",
    ],
)
def test_annotating_with_language_is_no_use_of_langcodes(source: str) -> None:
    assert list(_langcodes_uses(ast.parse(source))) == []


def test_langcodes_is_only_used_through_the_language_tags_module() -> None:
    package_path: Final = Path(backend.__file__).parent
    module_path: Final = Path(backend.language_tags.__file__)
    uses: Final = {
        str(path.relative_to(package_path)): sorted(set(_langcodes_uses(ast.parse(path.read_text(encoding="utf-8")))))
        for path in sorted(package_path.rglob("*.py"))
        if path != module_path
    }

    assert {path: names for path, names in uses.items() if names} == {}


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


@pytest.mark.parametrize(
    ("tag", "normalized"),
    [
        ("en-us", "en-US"),
        ("iw", "he"),
        ("x-foo", None),
        ("en_US", None),
    ],
)
def test_normalize_language_tag_normalizes_valid_tags_only(tag: str, normalized: str | None) -> None:
    assert normalize_language_tag(tag) == normalized


@pytest.mark.parametrize(
    ("stored", "requested"),
    [
        ("de", "de"),
        ("de", "DE"),
        ("en-us", "en-US"),
        ("en-US", "en-us"),
        # Deprecated language subtag.
        ("he", "iw"),
        ("iw", "he"),
    ],
)
def test_select_content_language_compares_normalized_tags(stored: str, requested: str) -> None:
    assert select_content_language({stored: "requested", "en": "English"}, requested) == (
        "requested",
        False,
    )


@pytest.mark.parametrize("requested", ["fr", "x-foo", "en_US"])
def test_select_content_language_falls_back_to_english(requested: str) -> None:
    assert select_content_language({"de": "German", "EN": "English"}, requested) == ("English", True)


def test_select_content_language_falls_back_to_the_first_content() -> None:
    assert select_content_language({"x-foo": "invalid", "de": "German"}, "fr") == ("invalid", True)


def test_select_content_language_never_matches_invalid_stored_tags() -> None:
    assert select_content_language({"de": "German", "en_US": "invalid"}, "en_US") == ("German", True)


def test_select_content_language_selects_the_first_of_equivalent_tags() -> None:
    assert select_content_language({"he": "first", "iw": "second"}, "iw") == ("first", False)


def test_select_content_language_rejects_missing_content() -> None:
    with pytest.raises(ValueError, match="at least one language"):
        _ = select_content_language(dict[str, str](), "en")


def test_parse_language_parses_the_tag_only_once(monkeypatch: pytest.MonkeyPatch) -> None:
    # Otherwise, the cache would be cleared if earlier tests had filled it up to the limit.
    monkeypatch.setattr(backend.language_tags, "_MAX_LANGCODES_CACHE_SIZE", sys.maxsize)
    cache: Final[object] = getattr(Language, "_PARSE_CACHE", None)
    assert isinstance(cache, Sized), "langcodes no longer provides `Language._PARSE_CACHE`"
    size_before: Final = len(cache)

    # Not normalized yet, so parsing the normalized tag again would add another entry.
    assert parse_language("de-at-x-once").to_tag() == "de-AT-x-once"

    assert len(cache) == size_before + 1


# `abcde` is structurally valid (language subtags of five to eight letters are reserved), but langcodes cannot parse it.
@pytest.mark.parametrize("tag", ["en_US", "abcde"])
def test_parse_language_rejects_invalid_tags(tag: str) -> None:
    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = parse_language(tag)


@pytest.mark.parametrize(("tag", "standardized"), [("en-us", "en-US"), ("en-Latn-US", "en-US"), ("iw", "he")])
def test_standardize_language_tag_returns_the_canonical_form(tag: str, standardized: str) -> None:
    assert standardize_language_tag(tag) == standardized


@pytest.mark.parametrize("tag", ["en_US", "i-klingon", "en-x-" + "-".join(["abcdefgh"] * 1000)])
def test_standardize_language_tag_rejects_invalid_tags_without_parsing_them(
    monkeypatch: pytest.MonkeyPatch, tag: str
) -> None:
    def _get(*_args: object, **_kwargs: object) -> Language:
        raise AssertionError("The tag must not be parsed.")

    monkeypatch.setattr(Language, "get", staticmethod(_get))

    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = standardize_language_tag(tag)


# Normalized to `sr-Latn-x-…`, which exceeds the length limit although the tag itself does not.
_LENGTHENED_BY_NORMALIZATION = "sh-x-" + "-".join(["abcdefgh"] * 6) + "-abcde"


def test_tags_whose_normalized_form_is_overlong_are_invalid() -> None:
    assert len(_LENGTHENED_BY_NORMALIZATION) == 64
    assert not is_valid_bcp_47_tag(_LENGTHENED_BY_NORMALIZATION)

    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = parse_language(_LENGTHENED_BY_NORMALIZATION)
    with pytest.raises(ValueError, match="Language must be a valid BCP 47 language tag"):
        _ = standardize_language_tag(_LENGTHENED_BY_NORMALIZATION)


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


def test_bcp_47_language_tag_keeps_the_original_spelling() -> None:
    assert _TAG_ADAPTER.validate_python("en-us") == "en-us"
    assert _TAG_ADAPTER.validate_python("iw") == "iw"


@pytest.mark.parametrize("value", ["en_US", "abc-123", "", "i-klingon", _LENGTHENED_BY_NORMALIZATION])
def test_bcp_47_language_tag_rejects_invalid_tags(value: str) -> None:
    with pytest.raises(ValidationError):
        _ = _TAG_ADAPTER.validate_python(value)


@pytest.mark.parametrize("locale", ["de-DE", "en", "en-US", "tr-TR", "haw", "zh-Hant-TW", "en-us"])
def test_valid_bcp_47_locales_are_accepted_and_preserved(locale: str) -> None:
    # `haw` is valid but is not one of the languages currently seeded by the UI.
    assert validate_locale(locale) == locale
    assert _LOCALE_ADAPTER.validate_python(locale) == locale


@pytest.mark.parametrize(
    "locale",
    ["", "en_US", "en--US", "not a locale", "abc-123", "i-klingon", "x-foo", "en-x-" + "-".join(["abcdefgh"] * 7)],
)
def test_invalid_locales_are_rejected(locale: str) -> None:
    with pytest.raises(ValueError, match="Locale must be a valid BCP 47 language tag"):
        _ = validate_locale(locale)
    with pytest.raises(ValidationError):
        _ = _LOCALE_ADAPTER.validate_python(locale)


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


@pytest.mark.parametrize(
    "tag", ["und", "und-DE", "und-x-foo", "qaa", "qtz-Latn", "qaa-DE", "mis", "mul", "zxx", "MUL", "QAA"]
)
def test_tags_without_a_particular_language_have_no_written_language(tag: str) -> None:
    assert written_language(parse_language(tag)) is None


# Real languages next to the private-use range (Quapaw, Quechua).
@pytest.mark.parametrize("tag", ["qua", "qu"])
def test_languages_outside_the_private_use_range_have_a_written_language(tag: str) -> None:
    assert written_language(parse_language(tag)) == (tag, "Latn")


@pytest.mark.parametrize(
    ("tag", "other_tag"),
    [("en-Qaaa", "en"), ("en-Qabx-US", "en-US"), ("sr-Qaaa", "sr-Cyrl"), ("zh-Zzzz-TW", "zh-Hant"), ("en-Zzzz", "en")],
)
def test_scripts_without_a_particular_script_are_replaced_with_the_likely_script(tag: str, other_tag: str) -> None:
    assert written_language(parse_language(tag)) == written_language(parse_language(other_tag))


# Rejected by `parse_language()`, since browsers do not accept them, but `Language` objects may still be created
# without validation.
@pytest.mark.parametrize("tag", ["x-foo", "x-pig-latin"])
def test_private_use_tags_have_no_written_language(tag: str) -> None:
    assert written_language(Language.get(tag)) is None
