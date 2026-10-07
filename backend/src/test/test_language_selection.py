from typing import Final
from typing import Optional

import pytest
from fastapi import Response
from langcodes import Language

import backend.language_selection
from backend.language_selection import LanguageRequest
from backend.language_selection import SelectedLanguage
from backend.language_selection import get_language_request
from backend.language_selection import select_language
from backend.language_selection import select_translation

_DE = Language.get("de")
_EN = Language.get("en")


@pytest.mark.asyncio
async def test_get_language_request_bundles_the_parameters() -> None:
    response: Final = Response()

    result: Final = await get_language_request(response, language="de", accept_language=["en"])

    assert result == LanguageRequest(response, language="de", accept_language="en")


@pytest.mark.asyncio
async def test_get_language_request_combines_several_accept_language_lines() -> None:
    response: Final = Response()

    result: Final = await get_language_request(response, accept_language=["fr", "de;q=0.9"])

    assert result == LanguageRequest(response, accept_language="fr, de;q=0.9")


@pytest.mark.asyncio
async def test_get_language_request_without_accept_language() -> None:
    response: Final = Response()

    result: Final = await get_language_request(response)

    assert result == LanguageRequest(response)


def test_select_language_describes_the_selection() -> None:
    response: Final = Response()

    result: Final = select_language([_DE, _EN], LanguageRequest(response, accept_language="de"))

    assert result == SelectedLanguage(language=_DE, is_language_fallback=False)
    assert response.headers["vary"] == "Accept-Language"


def test_select_language_rejects_missing_languages() -> None:
    with pytest.raises(ValueError, match="At least one language must be available"):
        _ = select_language([], LanguageRequest(Response(), language="de"))


def test_select_translation_rejects_missing_translations() -> None:
    response: Final = Response()
    translations_by_language: Final[dict[Language, str]] = {}

    with pytest.raises(ValueError, match="At least one language must be available"):
        _ = select_translation(translations_by_language, LanguageRequest(response, language="de", accept_language="de"))

    assert "vary" not in response.headers


def test_select_translation_returns_translation_and_language_details() -> None:
    result: Final = select_translation({_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), language="de"))

    assert result.translation == "Hallo"
    assert result.language_details.available_languages == [_DE, _EN]
    assert result.language_details.language_tag == _DE
    assert result.language_details.is_language_fallback is False


def test_select_translation_matches_canonical_form_of_more_specific_region() -> None:
    result: Final = select_translation(
        {Language.get("en-US"): "Howdy", _DE: "Hallo"}, LanguageRequest(Response(), accept_language="EN-us-x-private")
    )

    assert result.translation == "Howdy"
    assert result.language_details.language_tag == Language.get("en-US")
    assert result.language_details.is_language_fallback is False


def test_select_translation_returns_the_available_language_for_a_broader_match() -> None:
    result: Final = select_translation({_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), language="de-AT-1996"))

    assert result.translation == "Hallo"
    assert result.language_details.language_tag == _DE
    assert result.language_details.is_language_fallback is False


@pytest.mark.parametrize(
    ("language_tag", "available_tags", "expected_tag"),
    [
        # Truncated from the end, so the script is kept longer than the region.
        ("sr-Latn-RS", ["sr-RS", "sr-Latn"], "sr-Latn"),
        # Every variant is a truncation step of its own.
        ("de-CH-1901-1996", ["de", "de-CH-1901"], "de-CH-1901"),
        # Extensions are removed subtag by subtag, including their singletons.
        ("de-DE-u-co-phonebk", ["de", "de-DE"], "de-DE"),
    ],
)
def test_select_translation_follows_rfc_4647_lookup(
    language_tag: str, available_tags: list[str], expected_tag: str
) -> None:
    result: Final = select_translation(
        {Language.get(tag): tag for tag in available_tags}, LanguageRequest(Response(), language=language_tag)
    )

    assert result.translation == expected_tag
    assert result.language_details.is_language_fallback is False


@pytest.mark.parametrize(
    ("language_tag", "available_tags", "expected_tag"),
    [
        # Available languages may be more specific than the requested one.
        ("de", ["en", "de-DE"], "de-DE"),
        # Other regions of the same language match as well.
        ("de-AT", ["en", "de-DE"], "de-DE"),
        # A broader tag is preferred over a sibling region.
        ("de-AT", ["de-DE", "de"], "de"),
        # Of equally good matches, the first one is used.
        ("de", ["de-DE", "de-CH"], "de-DE"),
        ("de-AT", ["de-CH", "de-DE"], "de-CH"),
        # The likely script is part of the language: `zh-TW` is written in Traditional characters.
        ("zh-TW", ["zh-Hans", "zh-Hant"], "zh-Hant"),
        ("zh-Hant-HK", ["zh", "zh-TW"], "zh-TW"),
        # Matching languages share their script, so spelling it out does not affect which one is the closest.
        ("zh-TW", ["zh-Hant-HK", "zh-Hant-TW"], "zh-Hant-TW"),
        ("zh-Hant-TW", ["zh-HK", "zh-TW"], "zh-TW"),
        ("de-Latn-AT", ["de", "de-AT"], "de-AT"),
        ("de", ["de-AT", "de-Latn"], "de-Latn"),
        # Languages that CLDR's language matching treats as the same match each other.
        ("nb-NO", ["en", "no"], "no"),
        ("no", ["en", "nb-NO"], "nb-NO"),
        ("zsm", ["en", "ms"], "ms"),
        ("ar", ["en", "arb"], "arb"),
        ("cmn-TW", ["zh-Hans", "zh-Hant"], "zh-Hant"),
        # Their differing language subtags do not affect which language is the closest.
        ("nb-NO", ["no", "no-NO"], "no-NO"),
        ("cmn-TW", ["zh-Hant", "zh-TW"], "zh-TW"),
    ],
)
def test_select_translation_matches_the_same_written_language(
    language_tag: str, available_tags: list[str], expected_tag: str
) -> None:
    result: Final = select_translation(
        {Language.get(tag): tag for tag in available_tags}, LanguageRequest(Response(), language=language_tag)
    )

    assert result.translation == expected_tag
    assert result.language_details.is_language_fallback is False


@pytest.mark.parametrize(
    ("language_tag", "available_tags"),
    [
        # Different scripts are different written languages.
        ("zh-TW", ["en", "zh-Hans"]),
        ("sr-Latn", ["en", "sr-Cyrl"]),
        # Norwegian Nynorsk is not the same written language as Norwegian (Bokmål).
        ("nn", ["en", "no"]),
        ("nn", ["en", "nb"]),
        # Non-dominant languages of a macrolanguage are not the same as the macrolanguage.
        ("yue", ["en", "zh-Hant"]),
    ],
)
def test_select_translation_does_not_match_other_written_languages(
    language_tag: str, available_tags: list[str]
) -> None:
    result: Final = select_translation(
        {Language.get(tag): tag for tag in available_tags}, LanguageRequest(Response(), language=language_tag)
    )

    assert result.translation == "en"
    assert result.language_details.is_language_fallback is True


# `und` maximizes to `en-Latn-US`, but must not count as English.
def test_select_translation_ignores_available_languages_without_a_language() -> None:
    result: Final = select_translation(
        {Language.get("und"): "Undetermined", _DE: "Hallo"}, LanguageRequest(Response(), language="en")
    )

    assert result.translation == "Undetermined"
    assert result.language_details.is_language_fallback is True


@pytest.mark.parametrize(
    ("accept_language", "expected_translation", "is_language_fallback"),
    [
        (None, "Howdy", False),
        ("de", "Hallo", False),
        ("de-AT, de;q=0.9", "Hallo", False),
        ("fr", "Howdy", True),
    ],
)
def test_select_translation_finds_regional_content(
    accept_language: Optional[str], expected_translation: str, is_language_fallback: bool
) -> None:
    result: Final = select_translation(
        {Language.get("de-DE"): "Hallo", Language.get("en-US"): "Howdy"},
        LanguageRequest(Response(), accept_language=accept_language),
    )

    assert result.translation == expected_translation
    assert result.language_details.is_language_fallback is is_language_fallback


@pytest.mark.parametrize("available_tags", [["de", "en-GB"], ["de", "en-GB", "en"]])
def test_select_translation_falls_back_to_any_english(available_tags: list[str]) -> None:
    result: Final = select_translation({Language.get(tag): tag for tag in available_tags}, LanguageRequest(Response()))

    # Plain `en` is preferred if available.
    assert result.translation == available_tags[-1]


def test_select_translation_falls_back_to_header_when_route_language_is_unavailable() -> None:
    response: Final = Response()

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(response, language="fr", accept_language="de")
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"


# An invalid requested language must not fail the request, but it still expresses a preference that is not met.
@pytest.mark.parametrize("language", ["en_US", "jp", "not a tag", " "])
@pytest.mark.parametrize(("accept_language", "expected_translation"), [("de", "Hallo"), (None, "Hello")])
def test_select_translation_handles_invalid_route_language_like_an_unavailable_one(
    language: str, accept_language: Optional[str], expected_translation: str
) -> None:
    response: Final = Response()

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(response, language=language, accept_language=accept_language)
    )

    assert result.translation == expected_translation
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"


@pytest.mark.parametrize("accept_language", ["*, de;q=0.5", "not a tag!, de;q=0.5", "en;q=0, de;q=0.5"])
def test_select_translation_skips_wildcard_invalid_and_excluded_header_entries(accept_language: str) -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language=accept_language)
    )

    assert result.translation == "Hallo"


# Header entries are validated like the requested language, so invalid entries do not count as the first choice.
@pytest.mark.parametrize("accept_language", ["zz, de", "en_US, de", "jp;q=0.9, de;q=0.8"])
def test_select_translation_does_not_count_invalid_header_entries_as_first_choice(accept_language: str) -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language=accept_language)
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is False


@pytest.mark.parametrize(
    ("accept_language", "expected_translation"),
    [
        # Quality values take precedence over the order within the header.
        ("de;q=0.5, en;q=0.9", "Hello"),
        ("en;q=0.5, de", "Hallo"),
        # Entries of equal quality keep their order within the header.
        ("de;q=0.8, en;q=0.8", "Hallo"),
        ("en;q=0.8, de;q=0.8", "Hello"),
        ("en, de", "Hello"),
    ],
)
def test_select_translation_orders_header_entries_by_quality_then_position(
    accept_language: str, expected_translation: str
) -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language=accept_language)
    )

    assert result.translation == expected_translation
    assert result.language_details.is_language_fallback is False


def test_select_translation_only_considers_the_most_preferred_header_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(backend.language_selection, "_MAX_ACCEPT_LANGUAGE_ENTRIES", 2)

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language="de;q=0.1, fr, es;q=0.5")
    )

    assert result.translation == "Hello"
    assert result.language_details.is_language_fallback is True


def test_select_translation_stops_parsing_at_the_first_available_header_entry(monkeypatch: pytest.MonkeyPatch) -> None:
    parsed_tags: Final[list[str]] = []

    def _parse_valid_language(tag: str) -> Optional[Language]:
        parsed_tags.append(tag)
        return Language.get(tag)

    monkeypatch.setattr(backend.language_selection, "_parse_valid_language", _parse_valid_language)

    _ = select_translation({_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language="fr, de, es"))

    assert parsed_tags == ["fr", "de"]


def test_select_translation_prefers_header_entries_by_quality() -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), accept_language="fr;q=0.9, de;q=0.8, en;q=0.7")
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is True


# Without any usable preference, English (or the first available language) is not a fallback: there is no first
# choice that could have been unavailable. Wildcards, excluded languages (`q=0`), tags without a language (`und`), which
# cannot match any language, and an empty requested language (`?language=`) are ignored.
@pytest.mark.parametrize("language", [None, "", "und", "und-x-private"])
@pytest.mark.parametrize("accept_language", [None, "", "*", "!!!", "en;q=0", "und", "und-DE"])
@pytest.mark.parametrize(
    ("translations_by_language", "expected_language"),
    [({_DE: "Hallo", _EN: "Hello"}, _EN), ({_DE: "Hallo", Language.get("es"): "Hola"}, _DE)],
)
def test_select_translation_without_preference_is_no_fallback(
    language: Optional[str],
    accept_language: Optional[str],
    translations_by_language: dict[Language, str],
    expected_language: Language,
) -> None:
    response: Final = Response()

    result: Final = select_translation(
        translations_by_language, LanguageRequest(response, language=language, accept_language=accept_language)
    )

    assert result.translation == translations_by_language[expected_language]
    assert result.language_details.language_tag == expected_language
    assert result.language_details.is_language_fallback is False
    # A usable header would have changed the selection.
    assert response.headers["vary"] == "Accept-Language"


def test_select_translation_with_empty_requested_language_uses_header_without_fallback() -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), language="", accept_language="de")
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is False


@pytest.mark.parametrize(("language", "accept_language"), [(None, "und, de"), ("und", "de")])
def test_select_translation_does_not_count_tags_without_a_language_as_first_choice(
    language: Optional[str], accept_language: str
) -> None:
    result: Final = select_translation(
        {Language.get("und"): "Undetermined", _DE: "Hallo"},
        LanguageRequest(Response(), language=language, accept_language=accept_language),
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is False


def test_select_translation_appends_to_existing_vary_header() -> None:
    response: Final = Response(headers={"Vary": "Cookie"})

    _ = select_translation({_EN: "Hello"}, LanguageRequest(response))

    assert response.headers["vary"] == "Cookie, Accept-Language"


def test_select_translation_finds_translations_of_unnormalized_languages() -> None:
    # Created without normalization, so it differs from the normalized `de-DE` that its tag is parsed into.
    unnormalized: Final = Language.make(language="de", territory="de")

    result: Final = select_translation(
        {unnormalized: "Hallo", _EN: "Hello"}, LanguageRequest(Response(), language="de")
    )

    assert result.translation == "Hallo"
    assert result.language_details.language_tag == Language.get("de-DE")


def test_select_translation_falls_back_to_english_when_no_header_language_is_available() -> None:
    response: Final = Response()

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"}, LanguageRequest(response, accept_language="fr, es;q=0.5")
    )

    assert result.translation == "Hello"
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"
