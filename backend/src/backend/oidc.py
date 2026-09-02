from authlib.integrations.starlette_client import OAuth

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
