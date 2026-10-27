from typing import Final

import pytest

from backend.locales import locales_equivalent
from backend.locales import validate_locale
from backend.models.requests import UserPreferencesInputV1


@pytest.mark.parametrize(
    "locale",
    [
        "de-DE",
        "en",
        "en-US",
        "tr-TR",
        "haw",
        "zh-Hant-TW",
        "en-us",
        "es-419",
        "de-DE-1996",
        "en-US-u-ca-gregory",
        "en-t-de-1996",
        "en-US-x-private",
        # Structurally valid, although neither subtag is registered.
        "abc-123",
    ],
)
def test_valid_bcp_47_locales_are_accepted_and_preserved(locale: str) -> None:
    # `haw` is valid but is not one of the languages currently seeded by the UI.
    assert validate_locale(locale) == locale
    assert UserPreferencesInputV1(timezone="Europe/Berlin", locale=locale).locale == locale


@pytest.mark.parametrize("locale", ["", "en--US", "en-", "-en", "not a locale", "123", "x", "dé"])
def test_malformed_locales_are_rejected(locale: str) -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale(locale)


def test_non_ascii_locales_are_rejected() -> None:
    # Starts with KELVIN SIGN, whose lowercase form is `k`, so the tag would be accepted as `kin` otherwise.
    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale("Kin")


# `Intl` APIs of browsers throw on all of these.
@pytest.mark.parametrize(
    "locale",
    [
        # POSIX-style separator.
        "en_US",
        # Backward compatibility syntax.
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
def test_locales_that_browsers_reject_are_rejected(locale: str) -> None:
    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale(locale)


# Only private-use subtags may repeat singletons and other subtags.
def test_private_use_subtags_are_not_checked_for_duplicates() -> None:
    assert validate_locale("en-a-bbb-x-a-a-bbb") == "en-a-bbb-x-a-a-bbb"


_LONGEST_LOCALE = f"en-x-{'-'.join(['abcdefgh'] * 6)}-abcde"


def test_locales_of_the_maximum_length_are_accepted() -> None:
    assert len(_LONGEST_LOCALE) == 64
    assert validate_locale(_LONGEST_LOCALE) == _LONGEST_LOCALE


def test_overlong_locales_are_rejected() -> None:
    # Structurally valid, since private-use subtags may have up to eight characters.
    overlong: Final = _LONGEST_LOCALE + "f"

    with pytest.raises(ValueError, match="BCP 47"):
        _ = validate_locale(overlong)


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


def test_locales_equivalent_does_not_canonicalize() -> None:
    assert not locales_equivalent("en-Latn-US", "en-US")
