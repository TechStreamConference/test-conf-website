from typing import Final
from typing import final

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import StarletteOAuth2App
from pydantic import BaseModel
from pydantic import ConfigDict

from backend.config import SETTINGS

_ZITADEL_CLIENT_NAME = "zitadel"

# Requested at the authorization endpoint; `openid` is what makes this an OIDC
# rather than a plain OAuth2 flow.
_SCOPES = "openid profile email"

OAUTH = OAuth()

# The typeshed stubs leave `register` unannotated, so Pyright cannot type it.
OAUTH.register(  # type: ignore[reportUnknownMemberType, reportUnusedCallResult]
    name=_ZITADEL_CLIENT_NAME,
    server_metadata_url=f"{SETTINGS.zitadel_issuer.rstrip('/')}/.well-known/openid-configuration",
    client_id=SETTINGS.zitadel_client_id,
    client_secret=SETTINGS.zitadel_client_secret.get_secret_value(),
    client_kwargs={"scope": _SCOPES, "code_challenge_method": "S256"},
)


@final
class AuthorizationRequest(BaseModel):
    """Everything the login transaction needs to persist, plus the redirect target."""

    # Strict, because the values come from an untyped library rather than from user input.
    model_config = ConfigDict(frozen=True, strict=True)

    url: str
    state: str
    nonce: str
    code_verifier: str


async def create_authorization_request() -> AuthorizationRequest:
    """Build the ZITADEL authorization URL, generating state, nonce and PKCE verifier.

    Performs OIDC discovery against the issuer on first use.
    """
    client: Final[StarletteOAuth2App] = OAUTH.create_client(_ZITADEL_CLIENT_NAME)  # type: ignore[reportUnknownMemberType]
    result: Final = await client.create_authorization_url(  # type: ignore[reportUnknownMemberType, reportUnknownVariableType]
        redirect_uri=SETTINGS.zitadel_redirect_uri
    )

    return AuthorizationRequest.model_validate(result)  # type: ignore[reportUnknownArgumentType]
