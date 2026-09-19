from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

import backend.oidc as oidc_module
from backend.oidc import AuthorizationRequest
from backend.oidc import UserClaims
from backend.oidc import create_authorization_request
from backend.oidc import exchange_code


@pytest.mark.asyncio
async def test_create_authorization_request_uses_registered_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client: Final = Mock()
    client.create_authorization_url = AsyncMock(
        return_value={
            "url": "https://issuer.example/authorize",
            "state": "state",
            "nonce": "nonce",
            "code_verifier": "verifier",
        }
    )
    create_client: Final = Mock(return_value=client)
    monkeypatch.setattr(oidc_module.OAUTH, "create_client", create_client)

    result: Final = await create_authorization_request()

    assert result == AuthorizationRequest(
        url="https://issuer.example/authorize",
        state="state",
        nonce="nonce",
        code_verifier="verifier",
    )
    create_client.assert_called_once_with("zitadel")
    client.create_authorization_url.assert_awaited_once_with(redirect_uri=oidc_module.SETTINGS.zitadel_redirect_uri)


@pytest.mark.asyncio
@pytest.mark.parametrize("session_id", ["provider-session", None])
async def test_exchange_code_fetches_and_validates_id_token(
    monkeypatch: pytest.MonkeyPatch,
    session_id: str | None,
) -> None:
    token: Final = {"access_token": "token", "id_token": "encoded"}
    raw_claims: Final = {
        "sub": "provider-user",
        "email": "user@example.com",
        "email_verified": True,
        "preferred_username": "test-user",
    }
    if session_id is not None:
        raw_claims["sid"] = session_id
    client: Final = Mock()
    client.fetch_access_token = AsyncMock(return_value=token)
    client.parse_id_token = AsyncMock(return_value=raw_claims)
    create_client: Final = Mock(return_value=client)
    monkeypatch.setattr(oidc_module.OAUTH, "create_client", create_client)

    result: Final = await exchange_code("code", "verifier", "nonce")

    assert result == UserClaims(
        sub="provider-user",
        email="user@example.com",
        email_verified=True,
        preferred_username="test-user",
        sid=session_id,
    )
    create_client.assert_called_once_with("zitadel")
    client.fetch_access_token.assert_awaited_once_with(
        redirect_uri=oidc_module.SETTINGS.zitadel_redirect_uri,
        code="code",
        code_verifier="verifier",
    )
    client.parse_id_token.assert_awaited_once_with(token, nonce="nonce")
