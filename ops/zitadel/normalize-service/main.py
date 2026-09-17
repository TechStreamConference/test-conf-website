"""
ZITADEL Actions V2 response target for normalizing Twitch users.

Registered as a Response execution on:

    /zitadel.user.v2.UserService/RetrieveIdentityProviderIntent

The target enriches Twitch's sparse OIDC identity information using the
Twitch Helix API. In particular, it:

  * supplies the required givenName / familyName profile fields,
  * supplies Twitch's verified email address,
  * supplies the external IdP username required for linking,
  * gives newly created ZITADEL users a stable, collision-resistant username
    based on the immutable Twitch user ID.

For best results, configure the Twitch IdP in ZITADEL with:

  * Automatic creation: enabled
  * Account linking allowed: enabled
  * Automatic linking: email

With that configuration, an existing ZITADEL user with the same verified
email is linked before ZITADEL attempts to create another user.

ZITADEL sends an Actions V2 response target an envelope like:

    {
        "fullMethod": "...",
        "instanceID": "...",
        "orgID": "...",
        "request": {...},
        "response": {
            "idpInformation": {...},
            "createUser": {...}
        }
    }

For a REST Call target, the HTTP response MUST contain only the modified
API response object (`body["response"]`), not the complete Actions envelope.
"""

import json
import os
import sys
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any


EXPECTED_METHOD = "/zitadel.user.v2.UserService/RetrieveIdentityProviderIntent"

TWITCH_CLIENT_ID = os.environ.get("TWITCH_CLIENT_ID", "")
TWITCH_IDP_ID = os.environ.get("TWITCH_IDP_ID", "")
PORT = int(os.environ.get("PORT", "8080"))

TWITCH_USERS_URL = "https://api.twitch.tv/helix/users"


def _log(message: str, *, error: bool = False) -> None:
    print(
        f"[twitch-normalizer] {message}",
        file=sys.stderr if error else sys.stdout,
        flush=True,
    )


def _fetch_twitch_user(access_token: str) -> dict[str, Any]:
    """Fetch the Twitch user belonging to the supplied user access token."""
    request = urllib.request.Request(
        TWITCH_USERS_URL,
        headers={
            "Authorization": f"Bearer {access_token}",
            "Client-Id": TWITCH_CLIENT_ID,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            error_body = exc.read().decode("utf-8", errors="replace")
        except Exception:
            error_body = ""

        raise RuntimeError(
            f"Twitch Helix returned HTTP {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Unable to reach Twitch Helix: {exc}") from exc

    users = payload.get("data")
    if not isinstance(users, list) or not users:
        raise RuntimeError("Twitch Helix returned no user")

    user = users[0]
    if not isinstance(user, dict):
        raise RuntimeError("Twitch Helix returned an invalid user object")

    return user


def _build_zitadel_username(twitch_user_id: str) -> str:
    """
    Build the internal ZITADEL username for a Twitch-created account.

    The Twitch user ID is immutable, unlike the Twitch login name. Prefixing
    it with the provider name also prevents collisions with identities from
    other external providers using their own numeric IDs.
    """
    if not twitch_user_id:
        raise RuntimeError("Twitch did not return a user ID")

    return f"twitch-{twitch_user_id}"


def _set_idp_link_username(
    human: dict[str, Any],
    *,
    idp_id: str,
    idp_user_id: str,
    username: str,
) -> None:
    """
    Ensure the IDP link contains a non-empty userName.

    ZITADEL requires IDPLink.userName. Twitch's ID token does not currently
    provide preferred_username in this setup, so it is populated from Helix.
    """
    links = human.get("idpLinks")

    if not isinstance(links, list):
        links = []
        human["idpLinks"] = links

    for link in links:
        if not isinstance(link, dict):
            continue

        if link.get("idpId") == idp_id:
            link["userName"] = username
            return

    if idp_id and idp_user_id:
        links.append(
            {
                "idpId": idp_id,
                "userId": idp_user_id,
                "userName": username,
            }
        )


def _normalize_create_user(
    create_user: dict[str, Any],
    *,
    idp_id: str,
    idp_user_id: str,
    twitch_user_id: str,
    login: str,
    display_name: str,
    email: str,
) -> None:
    """Populate and normalize a CreateUserRequest."""
    human = create_user.get("human")
    if not isinstance(human, dict):
        raise RuntimeError("createUser does not contain a human user")

    profile = human.get("profile")
    if not isinstance(profile, dict):
        profile = {}
        human["profile"] = profile

    # Twitch does not expose given_name / family_name. Use its display name as
    # a harmless placeholder for ZITADEL's mandatory fields.
    profile["givenName"] = display_name
    profile["familyName"] = display_name
    profile["nickName"] = display_name
    profile["displayName"] = display_name

    email_object = human.get("email")
    if not isinstance(email_object, dict):
        email_object = {}
        human["email"] = email_object

    email_object["email"] = email

    # SetHumanEmail.verification is a protobuf oneof.
    email_object.pop("sendCode", None)
    email_object.pop("returnCode", None)

    # Twitch Helix documents this field as the user's verified email address
    # when user:read:email is granted.
    email_object["isVerified"] = True

    _set_idp_link_username(
        human,
        idp_id=idp_id,
        idp_user_id=idp_user_id,
        username=login,
    )

    # Do NOT use the Twitch login as the ZITADEL username. Twitch names share
    # a namespace neither with local ZITADEL users nor with other providers.
    #
    # A stable provider-prefixed external ID prevents collisions such as:
    #
    #   local ZITADEL user: coder2k
    #   Twitch login:       coder2k
    #
    # If automatic linking by email finds an existing user, Login V2 links
    # that account before CreateUser is called, so this username is only used
    # for genuinely new accounts.
    create_user["username"] = _build_zitadel_username(twitch_user_id)


def _normalize_add_human_user(
    add_human_user: dict[str, Any],
    *,
    idp_id: str,
    idp_user_id: str,
    twitch_user_id: str,
    login: str,
    display_name: str,
    email: str,
) -> None:
    """
    Populate the deprecated AddHumanUserRequest form.

    v4.17.1 normally exposes createUser for Login V2, but
    RetrieveIdentityProviderIntentResponse still contains addHumanUser for
    backwards compatibility.
    """
    profile = add_human_user.get("profile")
    if not isinstance(profile, dict):
        profile = {}
        add_human_user["profile"] = profile

    profile["givenName"] = display_name
    profile["familyName"] = display_name
    profile["nickName"] = display_name
    profile["displayName"] = display_name

    email_object = add_human_user.get("email")
    if not isinstance(email_object, dict):
        email_object = {}
        add_human_user["email"] = email_object

    email_object["email"] = email
    email_object.pop("sendCode", None)
    email_object.pop("returnCode", None)
    email_object["isVerified"] = True

    _set_idp_link_username(
        add_human_user,
        idp_id=idp_id,
        idp_user_id=idp_user_id,
        username=login,
    )

    add_human_user["username"] = _build_zitadel_username(twitch_user_id)


def _normalize_response(response: dict[str, Any]) -> None:
    """Normalize a RetrieveIdentityProviderIntent response in place."""
    idp_information = response.get("idpInformation")
    if not isinstance(idp_information, dict):
        raise RuntimeError("response does not contain idpInformation")

    idp_id = str(idp_information.get("idpId") or "")

    # The Response Execution runs for every external IdP. Only normalize the
    # configured Twitch provider.
    if idp_id != TWITCH_IDP_ID:
        _log(f"skipping non-Twitch IdP id={idp_id!r}")
        return

    idp_user_id = str(idp_information.get("userId") or "")

    create_user = response.get("createUser")
    add_human_user = response.get("addHumanUser")

    # If ZITADEL already resolved the external identity to an existing linked
    # user, there is no prospective user object to normalize.
    if not isinstance(create_user, dict) and not isinstance(add_human_user, dict):
        _log(
            "Twitch identity already resolved to an existing ZITADEL user; "
            f"zitadel_user_id={response.get('userId')!r}"
        )
        return

    oauth = idp_information.get("oauth")
    if not isinstance(oauth, dict):
        raise RuntimeError("Twitch idpInformation does not contain OAuth data")

    access_token = oauth.get("accessToken") or oauth.get("access_token")
    if not isinstance(access_token, str) or not access_token:
        raise RuntimeError("Twitch OAuth access token is missing")

    twitch_user = _fetch_twitch_user(access_token)

    twitch_user_id = str(twitch_user.get("id") or "")
    login = str(twitch_user.get("login") or "")
    display_name = str(twitch_user.get("display_name") or login)
    email = str(twitch_user.get("email") or "")

    if not twitch_user_id:
        raise RuntimeError("Twitch did not return a user ID")

    if not login:
        raise RuntimeError("Twitch did not return a login name")

    if not display_name:
        raise RuntimeError("Twitch did not return a display name")

    if not email:
        raise RuntimeError(
            "Twitch did not return an email address; "
            "ensure the IdP requests user:read:email"
        )

    # The token and the IDP intent must refer to the same Twitch identity.
    if idp_user_id and idp_user_id != twitch_user_id:
        raise RuntimeError(
            "Twitch user ID returned by Helix does not match "
            "ZITADEL idpInformation.userId"
        )

    # This value is used by ZITADEL when creating/linking the IDP link.
    # It deliberately remains the human-readable Twitch login. It is separate
    # from the collision-resistant ZITADEL account username.
    idp_information["userName"] = login

    effective_idp_user_id = idp_user_id or twitch_user_id

    if isinstance(create_user, dict):
        _normalize_create_user(
            create_user,
            idp_id=idp_id,
            idp_user_id=effective_idp_user_id,
            twitch_user_id=twitch_user_id,
            login=login,
            display_name=display_name,
            email=email,
        )
        zitadel_username = create_user["username"]

    elif isinstance(add_human_user, dict):
        _normalize_add_human_user(
            add_human_user,
            idp_id=idp_id,
            idp_user_id=effective_idp_user_id,
            twitch_user_id=twitch_user_id,
            login=login,
            display_name=display_name,
            email=email,
        )
        zitadel_username = add_human_user["username"]

    else:
        raise AssertionError("unreachable")

    _log(
        f"normalized Twitch user={login!r} "
        f"zitadel_username={zitadel_username!r} "
        f"email_present={bool(email)} "
        f"idp_id={idp_id!r}"
    )


class _Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path == "/health":
            self._respond_text(200, "ok")
            return

        self._respond_text(404, "not found")

    def do_POST(self) -> None:
        if self.path != "/normalize":
            self._respond_text(404, "not found")
            return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw_body = self.rfile.read(content_length)

            body = json.loads(raw_body or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")

            full_method = str(body.get("fullMethod") or "")

            _log(f"received action fullMethod={full_method!r}")

            if full_method and full_method != EXPECTED_METHOD:
                raise RuntimeError(
                    f"unexpected Actions V2 method: {full_method!r}"
                )

            response = body.get("response")
            if not isinstance(response, dict):
                raise RuntimeError(
                    "Actions V2 request does not contain a response object"
                )

            _normalize_response(response)

            # ZITADEL expects the modified RPC response itself, not the
            # surrounding Actions V2 request envelope.
            self._respond_json(200, response)

        except json.JSONDecodeError as exc:
            _log(f"invalid JSON request: {exc}", error=True)
            self._respond_text(400, "invalid JSON")

        except Exception as exc:
            # During setup, keep Interrupt on Error enabled in ZITADEL and fail
            # loudly so configuration/API errors are visible immediately.
            _log(f"ERROR: {exc}", error=True)
            self._respond_text(500, str(exc))

    def _respond_json(self, status: int, value: Any) -> None:
        body = json.dumps(
            value,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_text(self, status: int, value: str) -> None:
        body = value.encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args: Any) -> None:
        # Suppress BaseHTTPRequestHandler's default access log. Relevant
        # requests and errors are logged explicitly above.
        pass


def main() -> None:
    if not TWITCH_CLIENT_ID:
        raise SystemExit("TWITCH_CLIENT_ID is required")

    if not TWITCH_IDP_ID:
        raise SystemExit(
            "TWITCH_IDP_ID is required; set it to the ZITADEL ID of the "
            "instance-level Twitch identity provider"
        )

    server = ThreadingHTTPServer(("0.0.0.0", PORT), _Handler)

    _log(
        f"listening on :{PORT}; "
        f"Twitch ZITADEL IdP id={TWITCH_IDP_ID!r}"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
