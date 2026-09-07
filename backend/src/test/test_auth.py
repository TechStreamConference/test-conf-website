from datetime import timedelta
from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi import Response
from sqlalchemy.ext.asyncio import AsyncSession

import backend.routes.v1.auth as auth_module
from backend.models.tables import Account
from backend.models.tables import OidcLoginTransaction
from backend.oidc import AuthorizationRequest
from backend.oidc import UserClaims
from backend.routes.v1.auth import _is_valid_redirect_url  # type: ignore[reportPrivateUsage]
from backend.routes.v1.auth import callback
from backend.routes.v1.auth import login
from backend.routes.v1.auth import me
from backend.utils import hash_token
from backend.utils import utc_now

_TEST_BROWSER_VALUE = "browser-secret"


def _session() -> Mock:
    session: Final = Mock(spec=AsyncSession)
    session.commit = AsyncMock()
    session.delete = AsyncMock()
    session.get = AsyncMock()
    return session


def _transaction(*, browser_secret: str = _TEST_BROWSER_VALUE, expired: bool = False) -> OidcLoginTransaction:
    return OidcLoginTransaction(
        state_hash=hash_token("state"),
        browser_secret_hash=hash_token(browser_secret),
        nonce="nonce",
        pkce_code_verifier="verifier",
        return_to="https://frontend.example/events",
        expires_at=utc_now() + timedelta(minutes=-1 if expired else 10),
    )


def _claims(*, email_verified: bool = True) -> UserClaims:
    return UserClaims(
        sub="provider-user",
        email="user@example.com",
        email_verified=email_verified,
        preferred_username="test-user",
        sid="provider-session",
    )


@pytest.mark.parametrize(
    ("frontend_root_uri", "redirect_url", "expected"),
    [
        pytest.param(
            "https://frontend.example",
            "https://frontend.example",
            True,
            id="frontend-root",
        ),
        pytest.param(
            "https://frontend.example",
            "https://frontend.example/schedule",
            True,
            id="frontend-child-path",
        ),
        pytest.param(
            "https://frontend.example",
            "http://frontend.example/schedule",
            False,
            id="wrong-scheme",
        ),
        pytest.param(
            "https://frontend.example",
            "https://attacker.example/schedule",
            False,
            id="wrong-origin",
        ),
        pytest.param(
            "https://frontend.example/app",
            "https://frontend.example/app/page",
            True,
            id="configured-base-child-path",
        ),
        pytest.param(
            "https://frontend.example/app",
            "https://frontend.example/application",
            False,
            id="path-prefix-confusion",
        ),
    ],
)
def test_redirect_url_validation(
    monkeypatch: pytest.MonkeyPatch,
    frontend_root_uri: str,
    redirect_url: str,
    expected: bool,
) -> None:
    settings: Final = auth_module.SETTINGS.model_copy(update={"frontend_root_uri": frontend_root_uri})
    monkeypatch.setattr(auth_module, "SETTINGS", settings)

    assert _is_valid_redirect_url(redirect_url) is expected


@pytest.mark.asyncio
async def test_login_rejects_external_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    settings: Final = auth_module.SETTINGS.model_copy(update={"frontend_root_uri": "https://frontend.example"})
    monkeypatch.setattr(auth_module, "SETTINGS", settings)
    session: Final = _session()

    with pytest.raises(HTTPException) as exc_info:
        _ = await login("https://attacker.example", session)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid redirect URL."
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_login_persists_transaction_and_sets_secure_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    settings: Final = auth_module.SETTINGS.model_copy(update={"frontend_root_uri": "https://frontend.example"})
    monkeypatch.setattr(auth_module, "SETTINGS", settings)
    authorization_request: Final = AuthorizationRequest(
        url="https://issuer.example/authorize",
        state="state",
        nonce="nonce",
        code_verifier="verifier",
    )
    monkeypatch.setattr(auth_module, "create_authorization_request", AsyncMock(return_value=authorization_request))
    monkeypatch.setattr(auth_module, "generate_browser_secret", Mock(return_value="browser-secret"))
    session: Final = _session()

    response: Final = await login("https://frontend.example/events", session)  # type: ignore[arg-type]

    assert response.status_code == 302
    assert response.headers["location"] == authorization_request.url
    cookie: Final = response.headers["set-cookie"]
    assert "__Host-login=browser-secret" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    transaction: Final = session.add.call_args.args[0]
    assert isinstance(transaction, OidcLoginTransaction)
    assert transaction.state_hash == hash_token("state")
    assert transaction.browser_secret_hash == hash_token("browser-secret")
    assert transaction.nonce == "nonce"
    assert transaction.pkce_code_verifier == "verifier"
    assert transaction.return_to == "https://frontend.example/events"
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_callback_rejects_identity_provider_error() -> None:
    session: Final = _session()

    with pytest.raises(HTTPException) as exc_info:
        _ = await callback(Response(), session, error="access_denied")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "The identity provider did not authenticate the user."
    session.get.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("state", "code", "login_secret"),
    [
        (None, "code", "secret"),
        ("state", None, "secret"),
        ("state", "code", None),
    ],
)
async def test_callback_rejects_missing_transaction_inputs(
    state: str | None,
    code: str | None,
    login_secret: str | None,
) -> None:
    session: Final = _session()

    with pytest.raises(HTTPException) as exc_info:
        _ = await callback(Response(), session, login_secret, state, code)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "Invalid or expired login transaction."
    session.get.assert_not_awaited()


@pytest.mark.asyncio
async def test_callback_rejects_unknown_transaction() -> None:
    session: Final = _session()
    session.get.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        _ = await callback(Response(), session, "browser-secret", "state", "code")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    session.get.assert_awaited_once_with(OidcLoginTransaction, hash_token("state"))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("transaction", "login_secret"),
    [
        (_transaction(expired=True), "browser-secret"),
        (_transaction(), "wrong-secret"),
    ],
)
async def test_callback_consumes_invalid_transaction(
    transaction: OidcLoginTransaction,
    login_secret: str,
) -> None:
    session: Final = _session()
    session.get.return_value = transaction

    with pytest.raises(HTTPException) as exc_info:
        _ = await callback(Response(), session, login_secret, "state", "code")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 400
    session.delete.assert_awaited_once_with(transaction)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_callback_rejects_unverified_email_after_consuming_transaction(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transaction: Final = _transaction()
    session: Final = _session()
    session.get.return_value = transaction
    exchange: Final = AsyncMock(return_value=_claims(email_verified=False))
    monkeypatch.setattr(auth_module, "exchange_code", exchange)

    with pytest.raises(HTTPException) as exc_info:
        _ = await callback(Response(), session, "browser-secret", "state", "code")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "The email address of this account is not verified."
    exchange.assert_awaited_once_with(code="code", code_verifier="verifier", nonce="nonce")
    session.delete.assert_awaited_once_with(transaction)


@pytest.mark.asyncio
async def test_callback_creates_user_and_session_and_clears_login_cookie(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    transaction: Final = _transaction()
    claims: Final = _claims()
    session: Final = _session()
    session.get.return_value = transaction
    exchange: Final = AsyncMock(return_value=claims)
    find_user: Final = AsyncMock(return_value=42)
    create_user_session: Final = AsyncMock()
    monkeypatch.setattr(auth_module, "exchange_code", exchange)
    monkeypatch.setattr(auth_module, "find_or_create_user", find_user)
    monkeypatch.setattr(auth_module, "create_session", create_user_session)
    response: Final = Response()

    result: Final = await callback(response, session, "browser-secret", "state", "code")  # type: ignore[arg-type]

    assert result.redirect_url == "https://frontend.example/events"
    session.delete.assert_awaited_once_with(transaction)
    session.commit.assert_awaited_once()
    find_user.assert_awaited_once_with(session, claims)
    create_user_session.assert_awaited_once_with(
        session,
        response,
        user_id=42,
        zitadel_session_id="provider-session",
    )
    cookie: Final = response.headers["set-cookie"]
    assert "__Host-login=" in cookie
    assert "Max-Age=0" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie


@pytest.mark.asyncio
async def test_me_maps_current_account() -> None:
    account: Final = Account(
        user_id=42,
        zitadel_user_id="provider-user",
        email="user@example.com",
        username="test-user",
    )

    result: Final = await me(account)

    assert result.model_dump() == {
        "id": 42,
        "email": "user@example.com",
        "username": "test-user",
    }
