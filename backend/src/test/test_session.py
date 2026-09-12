from datetime import timedelta
from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from fastapi import HTTPException
from fastapi import Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

import backend.session as session_module
from backend.models.tables import Account
from backend.models.tables import User
from backend.models.tables import UserSession
from backend.oidc import UserClaims
from backend.session import SESSION_COOKIE_NAME
from backend.session import create_session
from backend.session import find_or_create_user
from backend.session import get_current_user
from backend.utils import hash_token
from backend.utils import utc_now


def _db() -> Mock:
    db: Final = Mock(spec=AsyncSession)
    db.execute = AsyncMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    return db


def _claims() -> UserClaims:
    return UserClaims(
        sub="provider-user",
        email="new@example.com",
        email_verified=True,
        preferred_username="new-name",
    )


def _result_with_optional(value: object) -> Mock:
    return Mock(scalar_one_or_none=Mock(return_value=value))


def _valid_session(now_offset: timedelta = timedelta()) -> UserSession:
    now: Final = utc_now() + now_offset
    return UserSession(
        id=1,
        user_id=42,
        token_hash=hash_token("session-token"),
        last_seen_at=now,
        expires_at=now + timedelta(days=1),
        absolute_expires_at=now + timedelta(days=30),
    )


@pytest.mark.asyncio
async def test_find_or_create_user_updates_existing_account() -> None:
    account: Final = Account(
        user_id=42,
        zitadel_user_id="provider-user",
        email="old@example.com",
        username="old-name",
    )
    db: Final = _db()
    db.execute.return_value = _result_with_optional(account)

    result: Final = await find_or_create_user(db, _claims())  # type: ignore[arg-type]

    assert result == 42
    assert account.email == "new@example.com"
    assert account.username == "new-name"
    db.add.assert_called_once_with(account)
    db.commit.assert_awaited_once()
    db.flush.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_or_create_user_creates_user_and_account() -> None:
    db: Final = _db()
    db.execute.return_value = _result_with_optional(None)

    async def assign_user_id() -> None:
        user: Final = db.add.call_args_list[0].args[0]
        assert isinstance(user, User)
        user.id = 42

    db.flush.side_effect = assign_user_id

    result: Final = await find_or_create_user(db, _claims())  # type: ignore[arg-type]

    assert result == 42
    assert db.add.call_count == 2
    account: Final = db.add.call_args_list[1].args[0]
    assert isinstance(account, Account)
    assert account.user_id == 42
    assert account.zitadel_user_id == "provider-user"
    assert account.email == "new@example.com"
    assert account.username == "new-name"
    db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_find_or_create_user_rejects_flushed_user_without_id() -> None:
    db: Final = _db()
    db.execute.return_value = _result_with_optional(None)

    with pytest.raises(ValueError, match="always has an id"):
        _ = await find_or_create_user(db, _claims())  # type: ignore[arg-type]

    db.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_find_or_create_user_recovers_from_concurrent_creation() -> None:
    db: Final = _db()
    db.execute.side_effect = [
        _result_with_optional(None),
        Mock(scalar_one=Mock(return_value=99)),
    ]

    async def assign_user_id() -> None:
        user: Final = db.add.call_args_list[0].args[0]
        assert isinstance(user, User)
        user.id = 42

    db.flush.side_effect = assign_user_id
    db.commit.side_effect = IntegrityError("insert", {}, Exception("duplicate"))

    result: Final = await find_or_create_user(db, _claims())  # type: ignore[arg-type]

    assert result == 99
    db.rollback.assert_awaited_once()
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_create_session_hashes_token_and_sets_secure_cookie(monkeypatch: pytest.MonkeyPatch) -> None:
    now: Final = utc_now()
    monkeypatch.setattr(session_module, "generate_session_token", Mock(return_value="plain-token"))
    monkeypatch.setattr(session_module, "utc_now", Mock(return_value=now))
    db: Final = _db()
    response: Final = Response()

    await create_session(
        db,  # type: ignore[arg-type]
        response,
        user_id=42,
        zitadel_session_id="provider-session",
    )

    stored: Final = db.add.call_args.args[0]
    assert isinstance(stored, UserSession)
    assert stored.user_id == 42
    assert stored.token_hash == hash_token("plain-token")
    assert stored.token_hash != "plain-token"
    assert stored.zitadel_session_id == "provider-session"
    assert stored.expires_at == now + timedelta(days=session_module.SETTINGS.session_idle_timeout_days)
    assert stored.absolute_expires_at == now + timedelta(days=session_module.SETTINGS.session_absolute_lifetime_days)
    db.commit.assert_awaited_once()
    cookie: Final = response.headers["set-cookie"]
    assert f"{SESSION_COOKIE_NAME}=plain-token" in cookie
    assert "HttpOnly" in cookie
    assert "Secure" in cookie
    assert "SameSite=lax" in cookie
    assert "Path=/" in cookie


@pytest.mark.asyncio
async def test_get_current_user_rejects_missing_cookie() -> None:
    db: Final = _db()

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_current_user(Response(), db)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated."
    db.execute.assert_not_awaited()


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_kind", ["unknown", "revoked", "idle-expired", "absolute-expired"])
async def test_get_current_user_rejects_invalid_sessions(
    monkeypatch: pytest.MonkeyPatch,
    invalid_kind: str,
) -> None:
    now: Final = utc_now()
    monkeypatch.setattr(session_module, "utc_now", Mock(return_value=now))
    db: Final = _db()
    user_session: UserSession | None = _valid_session()
    if invalid_kind == "unknown":
        user_session = None
    elif invalid_kind == "revoked":
        assert user_session is not None
        user_session.revoked_at = now
    elif invalid_kind == "idle-expired":
        assert user_session is not None
        user_session.expires_at = now - timedelta(seconds=1)
    else:
        assert user_session is not None
        user_session.absolute_expires_at = now - timedelta(seconds=1)
    db.execute.return_value = _result_with_optional(user_session)

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_current_user(Response(), db, "session-token")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401
    assert db.execute.await_count == 1


@pytest.mark.asyncio
async def test_get_current_user_rejects_session_without_account(monkeypatch: pytest.MonkeyPatch) -> None:
    now: Final = utc_now()
    monkeypatch.setattr(session_module, "utc_now", Mock(return_value=now))
    db: Final = _db()
    db.execute.side_effect = [
        _result_with_optional(_valid_session()),
        _result_with_optional(None),
    ]

    with pytest.raises(HTTPException) as exc_info:
        _ = await get_current_user(Response(), db, "session-token")  # type: ignore[arg-type]

    assert exc_info.value.status_code == 401
    assert db.execute.await_count == 2


@pytest.mark.asyncio
async def test_get_current_user_returns_account_without_refresh(monkeypatch: pytest.MonkeyPatch) -> None:
    now: Final = utc_now()
    monkeypatch.setattr(session_module, "utc_now", Mock(return_value=now))
    user_session: Final = _valid_session()
    account: Final = Account(
        user_id=42,
        zitadel_user_id="provider-user",
        email="user@example.com",
        username="test-user",
    )
    db: Final = _db()
    db.execute.side_effect = [
        _result_with_optional(user_session),
        _result_with_optional(account),
    ]
    response: Final = Response()

    result: Final = await get_current_user(response, db, "session-token")  # type: ignore[arg-type]

    assert result is account
    db.commit.assert_not_awaited()
    assert "set-cookie" not in response.headers


@pytest.mark.asyncio
async def test_get_current_user_refreshes_stale_session(monkeypatch: pytest.MonkeyPatch) -> None:
    now: Final = utc_now()
    monkeypatch.setattr(session_module, "utc_now", Mock(return_value=now))
    user_session: Final = _valid_session(now_offset=-timedelta(hours=2))
    account: Final = Account(
        user_id=42,
        zitadel_user_id="provider-user",
        email="user@example.com",
        username="test-user",
    )
    db: Final = _db()
    db.execute.side_effect = [
        _result_with_optional(user_session),
        _result_with_optional(account),
    ]
    response: Final = Response()

    result: Final = await get_current_user(response, db, "session-token")  # type: ignore[arg-type]

    assert result is account
    assert user_session.last_seen_at == now
    assert user_session.expires_at == now + timedelta(days=session_module.SETTINGS.session_idle_timeout_days)
    db.add.assert_called_once_with(user_session)
    db.commit.assert_awaited_once()
    assert f"{SESSION_COOKIE_NAME}=session-token" in response.headers["set-cookie"]
