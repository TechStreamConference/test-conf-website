from typing import Final
from typing import Optional

import pytest
from fastapi import Response
from langcodes import Language

import backend.language_selection
from backend.language_selection import select_translation

_DE = Language.get("de")
_EN = Language.get("en")


def test_select_translation_rejects_missing_translations() -> None:
    response: Final = Response()
    translations_by_language: Final[dict[Language, str]] = {}

    with pytest.raises(ValueError, match="At least one language must be available"):
        _ = select_translation(translations_by_language, language=_DE, accept_language="de", response=response)

    assert "vary" not in response.headers


def test_select_translation_returns_translation_and_language_details() -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=_DE,
        accept_language=None,
        response=Response(),
    )

    assert result.translation == "Hallo"
    assert result.language_details.available_languages == [_DE, _EN]
    assert result.language_details.language_tag == _DE
    assert result.language_details.is_language_fallback is False


def test_select_translation_matches_canonical_form_of_more_specific_region() -> None:
    result: Final = select_translation(
        {Language.get("en-US"): "Howdy", _DE: "Hallo"},
        language=None,
        accept_language="EN-us-x-private",
        response=Response(),
    )

    assert result.translation == "Howdy"
    assert result.language_details.language_tag == Language.get("en-US")
    assert result.language_details.is_language_fallback is False


def test_select_translation_returns_the_available_language_for_a_broader_match() -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=Language.get("de-AT-1996"),
        accept_language=None,
        response=Response(),
    )

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
        {Language.get(tag): tag for tag in available_tags},
        language=Language.get(language_tag),
        accept_language=None,
        response=Response(),
    )

    assert result.translation == expected_tag
    assert result.language_details.is_language_fallback is False


def test_select_translation_falls_back_to_header_when_route_language_is_unavailable() -> None:
    response: Final = Response()

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=Language.get("fr"),
        accept_language="de",
        response=response,
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"


@pytest.mark.parametrize("accept_language", ["*, de;q=0.5", "not a tag!, de;q=0.5", "en;q=0, de;q=0.5"])
def test_select_translation_skips_wildcard_invalid_and_excluded_header_entries(accept_language: str) -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=None,
        accept_language=accept_language,
        response=Response(),
    )

    assert result.translation == "Hallo"


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
        {_DE: "Hallo", _EN: "Hello"},
        language=None,
        accept_language=accept_language,
        response=Response(),
    )

    assert result.translation == expected_translation
    assert result.language_details.is_language_fallback is False


def test_select_translation_prefers_header_entries_by_quality() -> None:
    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=None,
        accept_language="fr;q=0.9, de;q=0.8, en;q=0.7",
        response=Response(),
    )

    assert result.translation == "Hallo"
    assert result.language_details.is_language_fallback is True


# Without any usable preference, English (or the first available language) is not a fallback: there is no first
# choice that could have been unavailable. Wildcards and excluded languages (`q=0`) are ignored.
@pytest.mark.parametrize("accept_language", [None, "", "*", "!!!", "en;q=0"])
@pytest.mark.parametrize(
    ("translations_by_language", "expected_language"),
    [({_DE: "Hallo", _EN: "Hello"}, _EN), ({_DE: "Hallo", Language.get("es"): "Hola"}, _DE)],
)
def test_select_translation_without_preference_is_no_fallback(
    accept_language: Optional[str],
    translations_by_language: dict[Language, str],
    expected_language: Language,
) -> None:
    response: Final = Response()

    result: Final = select_translation(
        translations_by_language,
        language=None,
        accept_language=accept_language,
        response=response,
    )

    assert result.translation == translations_by_language[expected_language]
    assert result.language_details.language_tag == expected_language
    assert result.language_details.is_language_fallback is False
    # A usable header would have changed the selection.
    assert response.headers["vary"] == "Accept-Language"


def test_select_translation_appends_to_existing_vary_header() -> None:
    response: Final = Response(headers={"Vary": "Cookie"})

    _ = select_translation({_EN: "Hello"}, language=None, accept_language=None, response=response)

    assert response.headers["vary"] == "Cookie, Accept-Language"


def test_select_translation_raises_if_selected_language_is_not_available(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def _determine_unavailable_language(
        **_: object,
    ) -> backend.language_selection._LanguageToBeDelivered:  # pyright: ignore[reportPrivateUsage]
        return backend.language_selection._LanguageToBeDelivered(  # pyright: ignore[reportPrivateUsage]
            language=Language.get("fr"),
            is_language_fallback=False,
            varies_with_accept_language=False,
        )

    monkeypatch.setattr(
        backend.language_selection,
        "_determine_language_to_be_delivered",
        _determine_unavailable_language,
    )

    with pytest.raises(RuntimeError):
        _ = select_translation({_DE: "Hallo"}, language=None, accept_language=None, response=Response())


def test_select_translation_falls_back_to_english_when_no_header_language_is_available() -> None:
    response: Final = Response()

    result: Final = select_translation(
        {_DE: "Hallo", _EN: "Hello"},
        language=None,
        accept_language="fr, es;q=0.5",
        response=response,
    )

    assert result.translation == "Hello"
    assert result.language_details.is_language_fallback is True
    assert response.headers["vary"] == "Accept-Language"
