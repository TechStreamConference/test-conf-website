import pytest

from backend.locales import canonical_locale
from backend.locales import locales_equivalent
from backend.locales import validate_locale
from backend.models.requests import UserPreferencesInputV1


@pytest.mark.parametrize("locale", ["de-DE", "en", "en-US", "tr-TR", "haw", "zh-Hant-TW"])
def test_valid_bcp_47_locales_are_accepted_and_preserved(locale: str) -> None:
    # `haw` is valid but is not one of the languages currently seeded by the UI.
    assert validate_locale(locale) == locale
    assert UserPreferencesInputV1(timezone="Europe/Berlin", locale=locale).locale == locale


@pytest.mark.parametrize("locale", ["", "en_US", "en--US", "not a locale", "abc-123"])
def test_invalid_locales_are_rejected(locale: str) -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale(locale)


@pytest.mark.parametrize(
    ("a", "b"),
    [
        ("en-us", "en-US"),
        ("EN-US", "en-US"),
        ("zh-Hant-TW", "zh-hant-tw"),
    ],
)
def test_locales_equivalent_ignores_casing(a: str, b: str) -> None:
    assert locales_equivalent(a, b)


def test_locales_equivalent_distinguishes_different_locales() -> None:
    assert not locales_equivalent("en-US", "en-GB")


def test_locales_equivalent_ignores_redundant_script() -> None:
    assert locales_equivalent("en-Latn-US", "en-US")


def test_canonical_locale_normalizes_casing() -> None:
    assert canonical_locale("en-us") == "en-US"


def test_canonical_locale_removes_redundant_script() -> None:
    assert canonical_locale("de-Latn-DE") == "de-DE"
