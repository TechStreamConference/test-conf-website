"""Keeps the supported display languages of the backend and of the frontend's Paraglide project in sync."""

import re
from pathlib import Path
from typing import Final
from typing import final

from pydantic import BaseModel
from pydantic import ConfigDict
from pydantic.alias_generators import to_camel

from backend.content_languages import ENGLISH_LANGUAGE_TAG
from backend.content_languages import SUPPORTED_DISPLAY_LANGUAGES
from backend.models.content_language_types import CONTENT_LANGUAGE_TAG_PATTERN

_SNAPSHOT_FILE = Path(__file__).resolve().parent / "supported_display_languages.snapshot"

# The settings file of the frontend's Paraglide project. Paraglide is the library that translates the user interface.
# It is part of the "inlang" toolkit, hence the name of the project directory, and reads the languages it provides
# translations for from this file.
_PARAGLIDE_SETTINGS_FILE = Path(__file__).resolve().parents[3] / "frontend" / "project.inlang" / "settings.json"


@final
class _ParaglideSettings(BaseModel):
    """The languages of the Paraglide project. The settings file uses camelCase names."""

    model_config = ConfigDict(alias_generator=to_camel)

    base_locale: str
    locales: list[str]


def _load_paraglide_settings() -> _ParaglideSettings:
    return _ParaglideSettings.model_validate_json(_PARAGLIDE_SETTINGS_FILE.read_text(encoding="utf-8"))


def test_supported_display_languages_are_the_locales_of_the_paraglide_project() -> None:
    frontend_languages: Final = frozenset(_load_paraglide_settings().locales)

    assert SUPPORTED_DISPLAY_LANGUAGES == frontend_languages, (
        "The supported display languages of the backend (`SUPPORTED_DISPLAY_LANGUAGES`) and the locales of the "
        + "frontend (`frontend/project.inlang/settings.json`) have to be the same. "
        + f"Missing in the frontend: {sorted(SUPPORTED_DISPLAY_LANGUAGES - frontend_languages)}. "
        + f"Missing in the backend: {sorted(frontend_languages - SUPPORTED_DISPLAY_LANGUAGES)}."
    )


def test_the_base_locale_of_the_paraglide_project_is_the_fallback_language_of_the_backend() -> None:
    settings: Final = _load_paraglide_settings()

    assert settings.base_locale == ENGLISH_LANGUAGE_TAG


def test_supported_display_languages_are_valid_content_language_tags() -> None:
    assert all(re.fullmatch(CONTENT_LANGUAGE_TAG_PATTERN, tag) for tag in SUPPORTED_DISPLAY_LANGUAGES)
    assert ENGLISH_LANGUAGE_TAG in SUPPORTED_DISPLAY_LANGUAGES


def _load_snapshot() -> frozenset[str]:
    return frozenset(_SNAPSHOT_FILE.read_text(encoding="utf-8").split())


def test_no_supported_display_language_is_removed() -> None:
    removed: Final = _load_snapshot() - SUPPORTED_DISPLAY_LANGUAGES

    assert not removed, (
        f"The display languages {sorted(removed)} are no longer supported. Users may have chosen them, and content "
        + "may rely on them, so a supported display language must never be removed."
    )


def test_every_supported_display_language_is_in_the_snapshot() -> None:
    added: Final = SUPPORTED_DISPLAY_LANGUAGES - _load_snapshot()

    assert not added, (
        f"Add the new display languages {sorted(added)} to {_SNAPSHOT_FILE.name}. The snapshot is what keeps the "
        + "supported display languages from shrinking."
    )
