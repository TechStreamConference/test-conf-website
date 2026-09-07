from datetime import timedelta
from typing import Annotated
from typing import Final
from typing import Optional

from fastapi import Cookie
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.config import SETTINGS
from backend.database import get_session
from backend.models.responses import NotAuthenticatedResponseV1
from backend.models.tables import Account
from backend.models.tables import User
from backend.models.tables import UserSession
from backend.oidc import UserClaims
from backend.utils import create_http_exception
from backend.utils import generate_session_token
from backend.utils import hash_token
from backend.utils import utc_now

# The `__Host-` prefix requires the cookie to be Secure, host-only and Path=/.
SESSION_COOKIE_NAME = "__Host-session"

# `last_seen_at`/`expires_at` are refreshed on this cadence rather than on every
# request, per the design doc.
_LAST_SEEN_REFRESH_INTERVAL = timedelta(hours=1)


def _set_session_cookie(response: Response, token: str, *, max_age: timedelta) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        max_age=int(max_age.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )


async def find_or_create_user(db: AsyncSession, claims: UserClaims) -> int:
    """Resolve the local user for a ZITADEL identity, creating both the user and
    its account on first login, or syncing mutable profile fields otherwise.

    Concurrent first logins for the same identity are resolved by retrying once
    after a unique-constraint violation: only one of them can win the race to
    create the account row, and the loser's speculative user row is rolled back
    along with it, so no orphaned user is left behind.
    """
    account: Final = (
        await db.execute(select(Account).where(Account.zitadel_user_id == claims.subject))
    ).scalar_one_or_none()
    if account is not None:
        account.email = claims.email
        account.username = claims.preferred_username
        db.add(account)
        await db.commit()
        return account.user_id

    user: Final = User()
    db.add(user)
    await db.flush()  # Assigns `user.id` without committing yet.
    if user.id is None:
        raise ValueError("A flushed user always has an id.")

    db.add(
        Account(
            user_id=user.id,
            zitadel_user_id=claims.subject,
            email=claims.email,
            username=claims.preferred_username,
        )
    )
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        return (await db.execute(select(Account.user_id).where(Account.zitadel_user_id == claims.subject))).scalar_one()

    return user.id


async def create_session(
    db: AsyncSession,
    response: Response,
    *,
    user_id: int,
    zitadel_session_id: Optional[str],
) -> None:
    """Issue a new application session and set its cookie."""
    token: Final = generate_session_token()
    now: Final = utc_now()
    idle_timeout: Final = timedelta(days=SETTINGS.session_idle_timeout_days)

    db.add(
        UserSession(
            user_id=user_id,
            token_hash=hash_token(token),
            zitadel_session_id=zitadel_session_id,
            expires_at=now + idle_timeout,
            absolute_expires_at=now + timedelta(days=SETTINGS.session_absolute_lifetime_days),
        )
    )
    await db.commit()

    _set_session_cookie(response, token, max_age=idle_timeout)


async def get_current_user(
    response: Response,
    db: Annotated[AsyncSession, Depends(get_session)],
    session_token: Annotated[Optional[str], Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> Account:
    if session_token is None:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, NotAuthenticatedResponseV1())

    token_hash: Final = hash_token(session_token)
    user_session: Final = (
        await db.execute(select(UserSession).where(UserSession.token_hash == token_hash))
    ).scalar_one_or_none()

    now: Final = utc_now()
    if (
        user_session is None
        or user_session.revoked_at is not None
        or user_session.expires_at < now
        or user_session.absolute_expires_at < now
    ):
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, NotAuthenticatedResponseV1())

    # Guaranteed to exist: a session is only ever created for a user that just
    # logged in, which always has an account.
    account: Final = (
        await db.execute(select(Account).where(Account.user_id == user_session.user_id))
    ).scalar_one_or_none()
    if account is None:
        raise create_http_exception(status.HTTP_401_UNAUTHORIZED, NotAuthenticatedResponseV1())

    if now - user_session.last_seen_at > _LAST_SEEN_REFRESH_INTERVAL:
        idle_timeout: Final = timedelta(days=SETTINGS.session_idle_timeout_days)
        user_session.last_seen_at = now
        user_session.expires_at = now + idle_timeout
        db.add(user_session)
        await db.commit()
        _set_session_cookie(response, session_token, max_age=idle_timeout)

    return account
