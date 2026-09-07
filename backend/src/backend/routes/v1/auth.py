import hmac
from typing import Annotated
from typing import Final
from typing import Optional
from urllib.parse import urlparse

from fastapi import APIRouter
from fastapi import Cookie
from fastapi import Depends
from fastapi import Response
from fastapi import status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import SETTINGS
from backend.database import get_session
from backend.models.responses import EmailNotVerifiedResponseV1
from backend.models.responses import IdentityProviderErrorResponseV1
from backend.models.responses import InvalidLoginTransactionResponseV1
from backend.models.responses import InvalidRedirectUrlResponseV1
from backend.models.responses import LoginCallbackResponseV1
from backend.models.responses import MeResponseV1
from backend.models.responses import NotAuthenticatedResponseV1
from backend.models.tables import Account
from backend.models.tables import OidcLoginTransaction
from backend.oidc import LOGIN_TRANSACTION_LIFETIME
from backend.oidc import create_authorization_request
from backend.oidc import exchange_code
from backend.session import create_session
from backend.session import find_or_create_user
from backend.session import get_current_user
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


@ROUTER.get(
    "/callback",
    summary="Identity provider callback endpoint",
    description="Completes the login started at the identity provider and returns the redirect target.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {
            "model": InvalidLoginTransactionResponseV1,
            "description": "Returned when the login transaction is unknown, expired or was started by another browser.",
        },
        status.HTTP_401_UNAUTHORIZED: {
            "model": IdentityProviderErrorResponseV1,
            "description": "Returned when the identity provider reported an error instead of an authorization code.",
        },
        status.HTTP_403_FORBIDDEN: {
            "model": EmailNotVerifiedResponseV1,
            "description": "Returned when the authenticated account has an unverified email address.",
        },
    },
    operation_id="login callback v1",
)
async def callback(
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
    login_secret: Annotated[Optional[str], Cookie(alias=_LOGIN_COOKIE_NAME)] = None,
    state: Optional[str] = None,
    code: Optional[str] = None,
    error: Optional[str] = None,
) -> LoginCallbackResponseV1:
    if error is not None:
        raise create_http_exception(
            status.HTTP_401_UNAUTHORIZED,
            IdentityProviderErrorResponseV1(),
        )

    if state is None or code is None or login_secret is None:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidLoginTransactionResponseV1(),
        )

    transaction: Final = await session.get(OidcLoginTransaction, hash_token(state))
    if transaction is None:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidLoginTransactionResponseV1(),
        )

    expires_at: Final = transaction.expires_at
    browser_secret_hash: Final = transaction.browser_secret_hash
    nonce: Final = transaction.nonce
    code_verifier: Final = transaction.pkce_code_verifier
    return_to: Final = transaction.return_to

    # Consume before validating so that a transaction can never be replayed.
    await session.delete(transaction)
    await session.commit()

    if expires_at < utc_now() or not hmac.compare_digest(browser_secret_hash, hash_token(login_secret)):
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidLoginTransactionResponseV1(),
        )

    claims: Final = await exchange_code(code=code, code_verifier=code_verifier, nonce=nonce)
    if not claims.email_verified:
        raise create_http_exception(
            status.HTTP_403_FORBIDDEN,
            EmailNotVerifiedResponseV1(),
        )

    user_id: Final = await find_or_create_user(session, claims)
    await create_session(session, response, user_id=user_id, zitadel_session_id=claims.session_id)

    # `secure`/`httponly`/`samesite` are required here too: the `__Host-` prefix
    # mandates `Secure` on every Set-Cookie for the name, including deletions,
    # or the browser silently rejects the header and never clears the cookie.
    response.delete_cookie(_LOGIN_COOKIE_NAME, path="/", secure=True, httponly=True, samesite="lax")

    return LoginCallbackResponseV1(redirect_url=return_to)


@ROUTER.get(
    "/me",
    summary="Get the current user",
    description="Returns the local user derived from the current application session.",
    status_code=status.HTTP_200_OK,
    responses={
        # 401 exceptions are raised indirectly via the `get_current_user` dependency.
        status.HTTP_401_UNAUTHORIZED: {"model": NotAuthenticatedResponseV1},
    },
    operation_id="get current user v1",
)
async def me(current_account: Annotated[Account, Depends(get_current_user)]) -> MeResponseV1:
    return MeResponseV1(id=current_account.user_id, email=current_account.email, username=current_account.username)
