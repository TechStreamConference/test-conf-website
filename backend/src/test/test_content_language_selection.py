from typing import Final

import pytest

from backend.content_language_selection import ContentLanguageSelection
from backend.content_language_selection import is_supported_language_range
from backend.content_language_selection import select_content_language


@pytest.mark.parametrize(
    "language_range",
    ["de", "DE", "fil", "de-AT", "DE-at", "es-419", "sr-Latn", "zh-Hant-TW", "zz", "und"],
)
def test_supported_language_ranges(language_range: str) -> None:
    assert is_supported_language_range(language_range)


@pytest.mark.parametrize(
    "language_range",
    [
        pytest.param("", id="empty"),
        pytest.param("x-foo", id="private use"),
        pytest.param("*", id="wildcard"),
        pytest.param("d", id="primary language too short"),
        pytest.param("deut", id="primary language too long"),
        pytest.param("de_AT", id="underscore"),
        pytest.param("de-", id="trailing hyphen"),
        pytest.param("de-AT-Latn", id="region before script"),
        pytest.param("de-Latn-Latn", id="two scripts"),
        pytest.param("de-1996", id="variant"),
        pytest.param("de-u-co-phonebk", id="extension"),
        pytest.param("zh-yue", id="extended language"),
        pytest.param("i-klingon", id="grandfathered"),
        pytest.param("de-41", id="two-digit region"),
        pytest.param("de\n", id="trailing newline"),
        pytest.param(" de", id="leading space"),
        pytest.param("dé", id="non-ASCII letter"),
        pytest.param("de-KK", id="Kelvin sign that matches k case-insensitively"),
        pytest.param("de-٣٣٣", id="non-ASCII digits"),
        pytest.param("de-" + "a" * 62, id="longer than 64 characters"),
    ],
)
def test_unsupported_language_ranges(language_range: str) -> None:
    assert not is_supported_language_range(language_range)


@pytest.mark.parametrize(
    ("language_ranges", "expected_language", "expected_fallback"),
    [
        pytest.param(["de"], "de", False, id="de"),
        pytest.param(["de-AT"], "de", False, id="de-AT"),
        pytest.param(["DE-at"], "de", False, id="DE-at"),
        pytest.param(["fr"], "en", True, id="fr"),
        pytest.param(["zz"], "en", True, id="zz"),
        pytest.param(["und"], "en", True, id="und"),
        pytest.param([], "en", False, id="no preference"),
    ],
)
def test_select_content_language_follows_the_behavior_table(
    language_ranges: list[str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    assert select_content_language(language_ranges, {"de", "en"}) == ContentLanguageSelection(
        language_tag=expected_language,
        available_languages=["de", "en"],
        is_language_fallback=expected_fallback,
    )


@pytest.mark.parametrize("language_range", ["ja", "JA", "Ja", "ja-JP", "JA-jp", "ja-Jpan", "ja-Jpan-JP"])
def test_select_content_language_compares_primary_language_subtags_case_insensitively(language_range: str) -> None:
    selection: Final = select_content_language([language_range], {"de", "en", "ja"})

    assert selection.language_tag == "ja"
    assert selection.is_language_fallback is False


def test_select_content_language_tries_preferences_in_order() -> None:
    selection: Final = select_content_language(["fr", "es-419", "de", "en"], {"de", "en", "es"})

    assert selection.language_tag == "es"
    assert selection.is_language_fallback is True


def test_select_content_language_ignores_unsupported_preferences() -> None:
    # Only the first supported preference decides whether the selection is a fallback.
    selection: Final = select_content_language(["x-foo", "*", "de-AT"], {"de", "en"})

    assert selection.language_tag == "de"
    assert selection.is_language_fallback is False


def test_select_content_language_without_supported_preferences_is_no_fallback() -> None:
    selection: Final = select_content_language(["x-foo", "*"], {"de", "en"})

    assert selection.language_tag == "en"
    assert selection.is_language_fallback is False


def test_select_content_language_defaults_to_the_first_language_without_english() -> None:
    selection: Final = select_content_language(["fr"], ["es", "de", "ja"])

    assert selection == ContentLanguageSelection(
        language_tag="de",
        available_languages=["de", "es", "ja"],
        is_language_fallback=True,
    )


def test_select_content_language_delivers_the_only_available_language() -> None:
    selection: Final = select_content_language(["en"], {"de"})

    assert selection.language_tag == "de"
    assert selection.available_languages == ["de"]
    assert selection.is_language_fallback is True


@pytest.mark.parametrize("language_ranges", [[], ["fr"], ["de"]])
def test_select_content_language_does_not_depend_on_the_order_of_available_languages(
    language_ranges: list[str],
) -> None:
    orders: Final = [["de", "es", "ja"], ["ja", "es", "de"], ["es", "ja", "de"]]

    selections: Final = [select_content_language(language_ranges, languages) for languages in orders]

    assert all(selection == selections[0] for selection in selections)
    assert selections[0].available_languages == ["de", "es", "ja"]


def test_select_content_language_requires_an_available_language() -> None:
    with pytest.raises(ValueError, match="At least one language must be available."):
        _ = select_content_language(["de"], [])
