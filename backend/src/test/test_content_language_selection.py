from collections.abc import AsyncGenerator
from collections.abc import Mapping
from typing import Final
from typing import NamedTuple
from typing import Optional
from typing import final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import Request
from fastapi import Response
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.content_language_selection import CONTENT_LANGUAGE_RESPONSE_HEADERS
from backend.content_language_selection import ContentLanguageSelection
from backend.content_language_selection import get_requested_language_ranges
from backend.content_language_selection import is_supported_language_range
from backend.content_language_selection import parse_accept_language
from backend.content_language_selection import select_content_language
from backend.database import get_session
from backend.main import app
from backend.models.responses import ImprintPageContentNotFoundResponseV1
from backend.models.responses import ImprintResponseV1
from backend.models.responses import UnsupportedLanguageTagResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind

# Longer than the 2 KiB that are considered, although every entry is supported.
_OVERSIZED_ACCEPT_LANGUAGE = ", ".join(["de"] * 1000)


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


@pytest.mark.parametrize(
    ("accept_language", "expected_language_ranges"),
    [
        pytest.param("", [], id="empty"),
        pytest.param("de", ["de"], id="single"),
        pytest.param("de;q=0.5, en;q=0.9", ["en", "de"], id="sorted by quality"),
        pytest.param("fr, de;q=0.8, es, en;q=0.8", ["fr", "es", "de", "en"], id="client order on ties"),
        pytest.param("de;q=0, en;q=0.5", ["en"], id="q=0 dropped"),
        pytest.param("de;q=0.000, en", ["en"], id="q=0.000 dropped"),
        pytest.param("de;q=abc, en;q=1.5, es;q=-1, fr", ["fr"], id="invalid q dropped"),
        pytest.param("fr, *;q=0.5", ["fr", "*"], id="wildcard kept"),
        pytest.param(" , ,de-CH,, en;q=0.8 ", ["de-CH", "en"], id="empty entries"),
        pytest.param(_OVERSIZED_ACCEPT_LANGUAGE, [], id="longer than 2 KiB"),
    ],
)
def test_parse_accept_language(accept_language: str, expected_language_ranges: list[str]) -> None:
    assert parse_accept_language(accept_language) == expected_language_ranges


def test_parse_accept_language_considers_a_header_of_exactly_2_kib() -> None:
    accept_language: Final = f"de, {'x' * 2044}"

    assert len(accept_language) == 2048
    assert parse_accept_language(accept_language)[0] == "de"


def test_parse_accept_language_considers_the_32_most_preferred_entries() -> None:
    entries: Final = [f"l{index:02}" for index in range(40)]

    # The least preferred entries come first, so that the cap must apply after sorting.
    accept_language: Final = ", ".join([*(f"{entry};q=0.5" for entry in entries[32:]), *entries[:32]])

    assert parse_accept_language(accept_language) == entries[:32]


def _page(language_tag: str) -> StaticPage:
    return StaticPage(
        kind=StaticPageKind.IMPRINT,
        language_tag=language_tag,
        content=f"Imprint ({language_tag})",
    )


@final
class _ContentResponse(NamedTuple):
    status_code: int
    body: object
    headers: Mapping[str, str]
    session: AsyncMock


def _get(
    path: str,
    available_languages: list[str],
    *,
    language: Optional[str] = None,
    accept_language: Optional[str | list[str]] = None,
) -> _ContentResponse:
    """Request a content route through the app, with an imprint in the available languages."""
    session: Final = AsyncMock(spec=AsyncSession)
    session.execute.return_value = Mock(scalars=Mock(return_value=[_page(tag) for tag in available_languages]))

    async def override_session() -> AsyncGenerator[AsyncSession]:
        yield session

    params: Final = {} if language is None else {"language": language}
    lines: Final = [accept_language] if isinstance(accept_language, str) else accept_language or []
    # Without an explicit header, the test client would send none either.
    headers: Final = [("Accept-Language", line) for line in lines]
    app.dependency_overrides[get_session] = override_session
    try:
        response: Final = TestClient(app).get(path, params=params, headers=headers)
    finally:
        _ = app.dependency_overrides.pop(get_session)
    return _ContentResponse(
        response.status_code,
        response.json(),
        response.headers,
        session,
    )


def _varies_by_accept_language(response: _ContentResponse) -> bool:
    return "accept-language" in (value.strip().lower() for value in response.headers.get("Vary", "").split(","))


@pytest.mark.parametrize(
    ("language", "accept_language", "available_languages", "expected_language", "expected_fallback"),
    [
        pytest.param(None, None, ["de", "en"], "en", False, id="no preference"),
        pytest.param("de", "en", ["de", "en"], "de", False, id="language=de overrides en"),
        pytest.param("de-AT", "en", ["de", "en"], "de", False, id="language=de-AT overrides en"),
        pytest.param("DE-at", None, ["de", "en"], "de", False, id="language=DE-at"),
        pytest.param("fr", "de", ["de", "en"], "en", True, id="language=fr overrides de"),
        pytest.param("zz", None, ["de", "en"], "en", True, id="language=zz"),
        pytest.param("und", None, ["de", "en"], "en", True, id="language=und"),
        pytest.param(None, "fr;q=0.9, de;q=0.8", ["de", "en"], "de", True, id="fr;q=0.9, de;q=0.8"),
        pytest.param(None, "de;q=0.5, en;q=0.9", ["de", "en"], "en", False, id="de;q=0.5, en;q=0.9"),
        pytest.param(None, "fr, de, en", ["de", "en"], "de", True, id="fr, de, en"),
        pytest.param(None, "de-CH, en;q=0.8", ["de", "en"], "de", False, id="de-CH, en;q=0.8"),
        pytest.param(None, "de;q=0, en;q=0.5", ["de", "en"], "en", False, id="de;q=0, en;q=0.5"),
        pytest.param(None, "de;q=0", ["de", "en"], "en", False, id="de;q=0"),
        pytest.param(None, "*", ["de", "en"], "en", False, id="*"),
        pytest.param(None, "fr, *;q=0.5", ["de", "en"], "en", True, id="fr, *;q=0.5"),
        pytest.param(None, "fr", ["de", "es"], "de", True, id="fr without English"),
        pytest.param(None, "de;q=abc", ["de", "en"], "en", False, id="invalid quality"),
        pytest.param(None, "de;q=2, en;q=-1", ["de", "en"], "en", False, id="quality out of range"),
        pytest.param(None, "x-foo, i-klingon", ["de", "en"], "en", False, id="unsupported ranges"),
        pytest.param(None, ";;, ,=", ["de", "en"], "en", False, id="garbage"),
        pytest.param(None, "", ["de", "en"], "en", False, id="empty header"),
        pytest.param(None, _OVERSIZED_ACCEPT_LANGUAGE, ["de", "en"], "en", False, id="longer than 2 KiB"),
        pytest.param(None, ", ".join(["x-foo"] * 31 + ["de"]), ["de", "en"], "de", False, id="32nd entry"),
        pytest.param(None, ", ".join(["x-foo"] * 32 + ["de"]), ["de", "en"], "en", False, id="33rd entry"),
        pytest.param(None, ["fr", "de"], ["de", "en"], "de", True, id="several field lines"),
    ],
)
def test_content_language_negotiation_follows_the_behavior_table(
    language: Optional[str],
    accept_language: Optional[str | list[str]],
    available_languages: list[str],
    expected_language: str,
    expected_fallback: bool,
) -> None:
    response: Final = _get(
        "/v1/imprint",
        available_languages,
        language=language,
        accept_language=accept_language,
    )

    assert response.status_code == 200
    imprint: Final = ImprintResponseV1.model_validate(response.body)
    assert imprint.content == f"Imprint ({expected_language})"
    assert imprint.language_details.language_tag == expected_language
    assert imprint.language_details.is_language_fallback is expected_fallback
    assert response.headers["Content-Language"] == expected_language
    # The selection depends on the header exactly if no language is given.
    assert _varies_by_accept_language(response) is (language is None)


@pytest.mark.parametrize(
    ("padding_length", "expected_language_ranges"),
    [
        pytest.param(2044, ["de", "ä" * 2044], id="2 KiB"),
        pytest.param(2045, [], id="longer than 2 KiB"),
    ],
)
def test_requested_language_ranges_bound_the_header_in_bytes(
    padding_length: int,
    expected_language_ranges: list[str],
) -> None:
    # A raw ASGI scope, because the test client would re-encode non-ASCII values as UTF-8.
    # Every non-ASCII Latin-1 character is a single byte on the wire.
    request: Final = Request({
        "type": "http",
        "headers": [(b"accept-language", f"de, {'ä' * padding_length}".encode("latin-1"))],
    })

    assert get_requested_language_ranges(request, Response()) == expected_language_ranges


def test_content_routes_answer_missing_content_with_not_found() -> None:
    response: Final = _get("/v1/imprint", [], language="de")

    assert response.status_code == 404
    assert ImprintPageContentNotFoundResponseV1.model_validate(response.body) == (
        ImprintPageContentNotFoundResponseV1()
    )
    assert "Content-Language" not in response.headers


@pytest.mark.parametrize("path", ["/v1/imprint", "/v1/event", "/v1/event/2024/1"])
@pytest.mark.parametrize("language", ["x-foo", ""])
def test_content_routes_answer_unsupported_languages_with_unprocessable_content(path: str, language: str) -> None:
    response: Final = _get(
        path,
        ["de", "en"],
        language=language,
        accept_language="de",
    )

    assert response.status_code == 422
    assert UnsupportedLanguageTagResponseV1.model_validate(response.body) == UnsupportedLanguageTagResponseV1()
    assert "Content-Language" not in response.headers
    response.session.execute.assert_not_awaited()


@pytest.mark.parametrize("path", ["/v1/imprint", "/v1/event", "/v1/event/{year}/{sequence_number}"])
def test_content_routes_document_the_content_language_response_headers(path: str) -> None:
    successful_response: Final = app.openapi()["paths"][path]["get"]["responses"]["200"]

    assert successful_response["headers"] == CONTENT_LANGUAGE_RESPONSE_HEADERS
    assert "application/json" in successful_response["content"]
