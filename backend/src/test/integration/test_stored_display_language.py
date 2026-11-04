from collections.abc import AsyncGenerator
from collections.abc import Callable
from collections.abc import Coroutine
from datetime import timedelta
from typing import Final
from typing import Optional

import httpx
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import col
from sqlmodel import delete

from backend.config import SETTINGS
from backend.models.responses import LanguageDetailsV1
from backend.models.tables import Account
from backend.models.tables import User
from backend.models.tables import UserDisplayLanguagePreference
from backend.models.tables import UserSession
from backend.session import SESSION_COOKIE_NAME
from backend.utils import generate_session_token
from backend.utils import hash_token
from backend.utils import utc_now

pytestmark: Final = [
    pytest.mark.integration,
    pytest.mark.usefixtures("migrate_and_seed_database"),
]

# Each of these seeded content elements is available in `de` and `en`.
_CONTENT_PATHS = ["/v1/event/2024/2", "/v1/imprint", "/v1/globals"]

# Creates a user with a session and the given stored display language, and returns the session cookie.
type _LogIn = Callable[[Optional[str]], Coroutine[None, None, dict[str, str]]]


@pytest_asyncio.fixture
async def log_in() -> AsyncGenerator[_LogIn]:
    engine: Final = create_async_engine(SETTINGS.database_url, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    user_ids: Final[list[int]] = []

    async def create_user_with_session(stored_language: Optional[str]) -> dict[str, str]:
        token: Final = generate_session_token()
        async with session_factory() as session:
            user: Final = User()
            session.add(user)
            await session.flush()
            assert user.id is not None
            user_ids.append(user.id)

            now: Final = utc_now()
            session.add(
                Account(
                    user_id=user.id,
                    zitadel_user_id=f"stored-display-language-test-{user.id}",
                    email="user@example.com",
                    username="test-user",
                ),
            )
            session.add(
                UserSession(
                    user_id=user.id,
                    token_hash=hash_token(token),
                    expires_at=now + timedelta(days=1),
                    absolute_expires_at=now + timedelta(days=30),
                ),
            )
            if stored_language is not None:
                session.add(UserDisplayLanguagePreference(user_id=user.id, language_tag=stored_language))
            await session.commit()
        return {SESSION_COOKIE_NAME: token}

    try:
        yield create_user_with_session
    finally:
        async with session_factory() as session:
            _ = await session.execute(
                delete(UserDisplayLanguagePreference).where(col(UserDisplayLanguagePreference.user_id).in_(user_ids)),
            )
            _ = await session.execute(delete(UserSession).where(col(UserSession.user_id).in_(user_ids)))
            _ = await session.execute(delete(Account).where(col(Account.user_id).in_(user_ids)))
            _ = await session.execute(delete(User).where(col(User.id).in_(user_ids)))
            await session.commit()
        await engine.dispose()


def _get(
    path: str,
    *,
    cookies: Optional[dict[str, str]] = None,
    language: Optional[str] = None,
    accept_language: Optional[str] = None,
) -> tuple[httpx.Response, LanguageDetailsV1]:
    headers: Final = {} if accept_language is None else {"Accept-Language": accept_language}
    if cookies is not None:
        # httpx deprecates cookies per request.
        headers["Cookie"] = "; ".join(f"{name}={value}" for name, value in cookies.items())
    response: Final = httpx.get(
        f"{SETTINGS.backend_root_uri}{path}",
        params={} if language is None else {"language": language},
        headers=headers,
    ).raise_for_status()
    return response, LanguageDetailsV1.model_validate(response.json()["languageDetails"])


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _CONTENT_PATHS)
@pytest.mark.parametrize("stored_language", ["de", "en"])
async def test_content_routes_prefer_the_stored_display_language_over_accept_language(
    log_in: _LogIn,
    path: str,
    stored_language: str,
) -> None:
    other_language: Final = "en" if stored_language == "de" else "de"

    response, language_details = _get(
        path,
        cookies=await log_in(stored_language),
        accept_language=other_language,
    )

    assert language_details.language_tag == stored_language
    assert language_details.is_language_fallback is False
    assert response.headers["Content-Language"] == stored_language
    assert "Accept-Language" in response.headers["Vary"]
    assert "Cookie" in response.headers["Vary"]
    assert response.headers["Cache-Control"] == "private"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _CONTENT_PATHS)
async def test_content_routes_report_an_unavailable_stored_display_language_as_fallback(
    log_in: _LogIn,
    path: str,
) -> None:
    _, language_details = _get(
        path,
        cookies=await log_in("fr"),
        accept_language="de",
    )

    assert language_details.language_tag == "en"
    assert language_details.is_language_fallback is True


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _CONTENT_PATHS)
async def test_content_routes_prefer_the_language_parameter_over_the_stored_display_language(
    log_in: _LogIn,
    path: str,
) -> None:
    response, language_details = _get(
        path,
        cookies=await log_in("de"),
        language="en",
    )

    assert language_details.language_tag == "en"
    assert language_details.is_language_fallback is False
    assert "Cookie" not in response.headers.get("Vary", "")
    assert "Cache-Control" not in response.headers


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _CONTENT_PATHS)
async def test_content_routes_negotiate_from_accept_language_without_a_stored_display_language(
    log_in: _LogIn,
    path: str,
) -> None:
    response, language_details = _get(
        path,
        cookies=await log_in(None),
        accept_language="de",
    )

    assert language_details.language_tag == "de"
    assert language_details.is_language_fallback is False
    assert response.headers["Cache-Control"] == "private"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", _CONTENT_PATHS)
async def test_content_routes_treat_an_invalid_session_like_an_anonymous_request(path: str) -> None:
    response, language_details = _get(
        path,
        cookies={SESSION_COOKIE_NAME: "invalid-session-token"},
        accept_language="de",
    )

    assert language_details.language_tag == "de"
    assert language_details.is_language_fallback is False
    assert "Cookie" in response.headers["Vary"]
    assert "Cache-Control" not in response.headers
