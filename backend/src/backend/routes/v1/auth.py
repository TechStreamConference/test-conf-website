from typing import Final
from urllib.parse import urlparse

from fastapi import APIRouter
from fastapi import status
from fastapi.responses import RedirectResponse

from backend.config import SETTINGS
from backend.models.responses import InvalidRedirectUrlResponseV1
from backend.utils import create_http_exception

ROUTER = APIRouter(prefix="/auth")


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
def login(redirect_url: str) -> RedirectResponse:
    if not _is_valid_redirect_url(redirect_url):
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            InvalidRedirectUrlResponseV1(),
        )
    # Set explicitly because `RedirectResponse` would otherwise default to 307.
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
