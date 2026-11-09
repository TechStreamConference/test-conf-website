from typing import Final

import pytest
from pydantic import ValidationError

from backend.models.responses import ContentLanguageV1
from backend.models.responses import LanguageDetailsV1


@pytest.mark.parametrize("language_tag", ["de", "en", "fil", "yue"])
def test_language_details_accept_content_languages(language_tag: str) -> None:
    details: Final = LanguageDetailsV1(
        available_languages=[ContentLanguageV1(language_tag=language_tag, name="Name")],
        language_tag=language_tag,
        is_language_fallback=False,
    )

    assert details.language_tag == language_tag
    assert details.available_languages[0].language_tag == language_tag


@pytest.mark.parametrize("language_tag", ["", "d", "DE", "De", "de-AT", "de_DE", "zh-Hant", "deut", "d1"])
def test_language_details_reject_other_tags(language_tag: str) -> None:
    with pytest.raises(ValidationError, match="String should match pattern"):
        _ = LanguageDetailsV1(
            available_languages=[ContentLanguageV1(language_tag="de", name="Deutsch")],
            language_tag=language_tag,
            is_language_fallback=False,
        )

    with pytest.raises(ValidationError, match="String should match pattern"):
        _ = ContentLanguageV1(language_tag=language_tag, name="Name")


def test_language_details_serialize_available_languages_with_their_names() -> None:
    details: Final = LanguageDetailsV1(
        available_languages=[
            ContentLanguageV1(language_tag="de", name="Deutsch"),
            ContentLanguageV1(language_tag="ja", name="日本語"),
        ],
        language_tag="ja",
        is_language_fallback=False,
    )

    assert details.model_dump(mode="json") == {
        "availableLanguages": [
            {"languageTag": "de", "name": "Deutsch"},
            {"languageTag": "ja", "name": "日本語"},
        ],
        "languageTag": "ja",
        "isLanguageFallback": False,
    }
