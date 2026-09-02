from typing import Annotated
from typing import Final
from urllib.parse import urlparse

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import SETTINGS
from backend.database import get_session
from backend.models.responses import InvalidRedirectUrlResponseV1
from backend.models.tables import OidcLoginTransaction
from backend.oidc import LOGIN_TRANSACTION_LIFETIME
from backend.oidc import create_authorization_request
from backend.utils import create_http_exception
from backend.utils import generate_browser_secret
from backend.utils import hash_token
from backend.utils import utc_now

ROUTER = APIRouter(prefix="/auth")

# The `__Host-` prefix requires the cookie to be Secure, host-only and Path=/.
_LOGIN_COOKIE_NAME = "__Host-login"


def _is_valid_redirect_url(redirect_url: str) -> bool:
    parsed: Final = urlparse(redirect_url)
    base: Final = urlparse(SETTINGS.frontend_root_uri)

    if parsed.scheme != base.scheme or parsed.netloc != base.netloc:
        return False

    base_path: Final = base.path.rstrip("/")

    return parsed.path == base_path or parsed.path.startswith(base_path)


@ROUTER.get(
    "/login",
    summary="User login endpoint",
    description="Forwards the client to the identity provider for authentication",
    status_code=status.HTTP_302_FOUND,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": InvalidRedirectUrlResponseV1,
            "description": (
                "Returned when the provided redirect URL points to a "
                + "location external to the frontend application."
            ),
        },
    },
    operation_id="login v1",
)
async def login(
    redirect_url: str,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> RedirectResponse:
    if not _is_valid_redirect_url(redirect_url):
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidRedirectUrlResponseV1(),
        )

    authorization_request: Final = await create_authorization_request()
    browser_secret: Final = generate_browser_secret()

    session.add(
        OidcLoginTransaction(
            state_hash=hash_token(authorization_request.state),
            browser_secret_hash=hash_token(browser_secret),
            nonce=authorization_request.nonce,
            pkce_code_verifier=authorization_request.code_verifier,
            return_to=redirect_url,
            expires_at=utc_now() + LOGIN_TRANSACTION_LIFETIME,
        )
    )
    await session.commit()

    # Set explicitly because `RedirectResponse` would otherwise default to 307.
    response: Final = RedirectResponse(url=authorization_request.url, status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=_LOGIN_COOKIE_NAME,
        value=browser_secret,
        max_age=int(LOGIN_TRANSACTION_LIFETIME.total_seconds()),
        httponly=True,
        secure=True,
        samesite="lax",
        path="/",
    )

    return response
