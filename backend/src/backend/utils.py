import hashlib
import secrets
from datetime import UTC
from datetime import datetime
from typing import Final

from fastapi import HTTPException
from pydantic import BaseModel

_BROWSER_SECRET_BYTES = 32
_SESSION_TOKEN_BYTES = 32


def utc_now() -> datetime:
    """Current UTC time, made naïve to match the timestamp columns."""
    return datetime.now(UTC).replace(tzinfo=None)


def generate_browser_secret() -> str:
    """Secret handed to the browser in the login cookie and stored hashed in the transaction.

    Binds the callback to the user agent that started the flow.
    """
    return secrets.token_urlsafe(_BROWSER_SECRET_BYTES)


def generate_session_token() -> str:
    """Opaque bearer token handed to the browser as the application session cookie.

    Only its hash is stored, so a database leak alone cannot yield a usable session.
    """
    return secrets.token_urlsafe(_SESSION_TOKEN_BYTES)


def hash_token(token: str) -> str:
    """Hash a bearer-style token for storage at rest."""
    # Plain SHA-256 suffices because these tokens are high-entropy random values,
    # so there is nothing for an attacker to brute-force.
    return hashlib.sha256(token.encode()).hexdigest()


def create_http_exception(status_code: int, body: BaseModel) -> HTTPException:
    """
    Create an `HTTPException` with a detail payload derived from a Pydantic model.
    Note: FastAPI wraps `exc.detail` into a top-level `{"detail": exc.detail}`. If the
    provided model only contains a `detail` field, we unwrap it to avoid returning
    `{"detail": {"detail": "..."}}`.
    """
    dumped: Final = body.model_dump()
    detail: Final = dumped["detail"] if set(dumped.keys()) == {"detail"} else dumped
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )
