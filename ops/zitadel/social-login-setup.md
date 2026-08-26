# Social Login Setup: Google and Twitch

This guide describes how to configure Google and Twitch as federated identity
providers (IdPs) for the self-hosted Zitadel instance at `https://id.test-conf.de/`
running Login V2.

No application code changes are required. Once an IdP is active in Zitadel the
Next.js login UI automatically shows the corresponding button.

---

## How it works

Zitadel acts as the OIDC broker. When a user clicks "Login with Google" or
"Login with Twitch", Zitadel redirects them to the external provider, receives
the callback, maps the external identity into its own user store, and issues its
own tokens to the application. The application only ever speaks to Zitadel.

### Account lifecycle

The goal is a single Zitadel account per human, regardless of how they first
signed up:

```text
                       ┌── username/password
                       │
one Zitadel user ──────┼── Google
                       │
                       └── Twitch
```

**Automatic creation** creates a new Zitadel user on the first external login.
**Automatic linking by email** links the external identity to an existing Zitadel
user instead of creating a duplicate, provided both share the same verified email
address.

Username-based automatic linking is not used. Twitch logins (and other external
usernames) share no namespace with local Zitadel usernames; matching on them
would produce false positives.

---

## Prerequisites

- Zitadel **v4.17.1** or later (pinned in `.env`). Earlier versions have a bug
  where automatic user creation fails when `givenName` or `familyName` is absent.
- Admin access to the Zitadel console at <https://id.test-conf.de/ui/console/>
- An OAuth 2.0 client registered at each provider (see the provider-specific
  sections below)

---

## 1. Required environment configuration

The `zitadel-login` service must have email verification enabled so that local
username/password registrations produce verified email addresses. Verified email
is the security boundary for automatic account linking.

In `compose.yml` (already configured):

```yaml
EMAIL_VERIFICATION: "true"
```

> Existing manually created users: being active in Zitadel does not imply that
> their email is verified. Check their profile in the Console before relying on
> automatic email-based linking for those accounts.

The `zitadel-api` service must be allowed to call the internal
`twitch-normalizer` container. Docker assigns container IPs from
`172.16.0.0/12`, which Zitadel's default SSRF protection blocks. The denylist
is overridden in `compose.yml` (already configured) to remove that range while
keeping all other private, loopback, and link-local ranges blocked:

```yaml
ZITADEL_HTTPCLIENT_DENYLIST: "localhost,0.0.0.0/8,10.0.0.0/8,100.64.0.0/10,127.0.0.0/8,169.254.0.0/16,192.168.0.0/16,198.18.0.0/15,::/128,::1/128,fc00::/7,fe80::/10"
```

---

## 2. Google

Google provides standard OIDC claims (`given_name`, `family_name`, `email`) so
Zitadel can create and link users automatically without additional infrastructure.

### 2.1 Register an OAuth client in Google Cloud Console

1. <https://console.cloud.google.com> → **APIs & Services** → **Credentials**
2. **Create Credentials** → **OAuth 2.0 Client ID**
3. Application type: **Web application**
4. **Authorized redirect URIs**:

    ```text
    https://id.test-conf.de/idps/callback
    ```

5. Save. Note down the **Client ID** and **Client Secret**.

### 2.2 Configure Google in Zitadel

1. **Instance** → **Identity Providers** → **New** → **Google**
2. Fill in:

   | Field                   | Value                                         |
   |-------------------------|-----------------------------------------------|
   | Client ID               | from step 2.1                                 |
   | Client Secret           | from step 2.1                                 |
   | Scopes                  | leave defaults (`openid`, `profile`, `email`) |
   | Automatic creation      | **enabled**                                   |
   | Automatic update        | **enabled**                                   |
   | Account linking allowed | **enabled**                                   |
   | Automatic linking       | **Email**                                     |

3. Save.

---

## 3. Twitch

Twitch is configured as a **Generic OIDC** provider. Its OIDC tokens do not
include the `given_name`, `family_name`, or `email` claims that Zitadel requires
for automatic human-user creation. A small internal service — the
**Twitch normalizer** — fills in those fields by calling the Twitch Helix API
before Zitadel creates or links the user.

The normalizer is invoked via an **Actions V2 Response execution** on the
`RetrieveIdentityProviderIntent` RPC. This is the correct extension point for
Login V2; V1 Actions do not run in the Login V2 flow.

### 3.1 Register an application in the Twitch Developer Console

1. <https://dev.twitch.tv/console> → **Register Your Application**
2. Fill in:

   | Field               | Value                                   |
   |---------------------|-----------------------------------------|
   | Name                | `test-conf.de`                          |
   | OAuth Redirect URLs | `https://id.test-conf.de/idps/callback` |
   | Category            | Website Integration                     |

3. Click **Manage** to reveal the **Client ID**.
4. Click **New Secret** to generate a **Client Secret**.
5. Note down the **Client ID** (also needed in `.env` as `TWITCH_CLIENT_ID`).

### 3.2 Configure Twitch in Zitadel

1. **Instance** → **Identity Providers** → **New** → **Generic OIDC**
2. Fill in:

   | Field                   | Value                         |
   |-------------------------|-------------------------------|
   | Name                    | `Twitch`                      |
   | Issuer                  | `https://id.twitch.tv/oauth2` |
   | Client ID               | from step 3.1                 |
   | Client Secret           | from step 3.1                 |
   | Scopes                  | `openid user:read:email`      |
   | Map from the ID token   | **enabled**                   |
   | Automatic creation      | **enabled**                   |
   | Automatic update        | **enabled**                   |
   | Account linking allowed | **enabled**                   |
   | Automatic linking       | **Email**                     |

   > Remove `profile` from Scopes if Zitadel pre-fills it — Twitch rejects
   > that scope.
   >
   > "Map from the ID token" must be enabled. Without it Zitadel calls Twitch's
   > userinfo endpoint directly, which returns HTTP 401 because Zitadel cannot
   > attach the required `Client-Id` header. With it enabled, the normalizer
   > calls the Helix API instead using the access token from the IdP intent.

3. Save. Copy the **IdP ID** from the URL after saving (e.g. `240527863549583361`).
   You will need it as `TWITCH_IDP_ID` in the next step.

### 3.3 Configure environment variables

Add both values to `ops/zitadel/.env` (see `.env.example` for the full template):

```ini
# Public identifier from the Twitch Developer Console.
TWITCH_CLIENT_ID=<client-id-from-step-3.1>

# Zitadel's internal ID for the Twitch IdP (from the URL after saving the IdP).
TWITCH_IDP_ID=<idp-id-from-step-3.2>
```

`TWITCH_CLIENT_ID` is a public identifier, not a secret. The normalizer sends it
as the `Client-Id` header when calling the Twitch Helix API.

`TWITCH_IDP_ID` tells the normalizer which IdP to handle. The same Actions V2
execution fires for every external provider; the normalizer ignores all IdPs
other than the one matching this ID.

Both variables are required. The normalizer exits at startup if either is
missing.

### 3.4 Deploy the normalizer

The normalizer (`normalize-service/main.py`) runs as a container inside the
Zitadel Compose stack with no external dependencies.

Start or restart the full stack:

```bash
cd ops/zitadel
docker compose up -d --wait
```

Verify the normalizer is healthy:

```bash
docker compose ps twitch-normalizer
# Expected: Up (healthy)

docker compose logs twitch-normalizer
# Expected: [twitch-normalizer] listening on :8080; Twitch ZITADEL IdP id='...'
```

The service is only reachable on the internal `zitadel` Docker network and is
never published to the host.

### 3.5 Create the Actions V2 Target

**Instance** → **Actions** → **Targets** → **Create**

| Field              | Value                                     |
| ------------------ | ----------------------------------------- |
| Name               | `twitch-normalizer`                       |
| Endpoint           | `http://twitch-normalizer:8080/normalize` |
| Type               | **REST Call**                             |
| Payload Type       | **JSON**                                  |
| Timeout            | `10`                                      |
| Interrupt on Error | **enabled**                               |

**REST Call** (not Webhook) is required because Zitadel reads and applies the
response body returned by the target.

**Interrupt on Error** should remain enabled. The normalizer returns HTTP 500 on
any configuration or API error; interrupting the login on error makes
misconfigurations immediately visible rather than silently producing incomplete
user records.

### 3.6 Create the Actions V2 Execution

**Instance** → **Actions** → **Create**

**Step 1 — When to run:** select **Response**, click **Continue**.

**Step 2 — Scope:** leave **All** unchecked. Fill in:

- **Select Service**: type `UserService` → select `zitadel.user.v2.UserService`
- **Select Method**: type `RetrieveIdentityProviderIntent` → select it

Click **Continue**.

**Step 3 — Target:** select `twitch-normalizer`, click **Continue** to save.

The executions list should show:

| Condition                                                              | Type     | Target             |
| ---------------------------------------------------------------------- | -------- | ------------------ |
| method: /zitadel.user.v2.UserService/RetrieveIdentityProviderIntent    | Response | twitch-normalizer  |

---

## 4. What the normalizer does

When Zitadel calls `/normalize`, the service:

1. Reads `body["response"]` from the Actions V2 envelope (Zitadel expects only
   the modified RPC response object in return, not the full envelope).
2. Checks `idpInformation.idpId`. If it does not match `TWITCH_IDP_ID`, returns
   the response unchanged.
3. If the external identity is already linked to a Zitadel user (no `createUser`
   field present), returns the response unchanged.
4. Extracts the OAuth access token from `idpInformation.oauth.accessToken`.
5. Calls `GET https://api.twitch.tv/helix/users` with that token and
   `TWITCH_CLIENT_ID` as the `Client-Id` header.
6. Populates the `createUser` object:
   - `givenName`, `familyName`, `nickName`, `displayName` — Twitch display name
     (Twitch exposes no given/family name; the display name is a valid placeholder)
   - `email` + `isVerified: true` — Twitch Helix returns the user's verified
     email when `user:read:email` is granted
   - `username` — `twitch-{twitch_user_id}` — immutable and collision-resistant;
     avoids conflicts with local accounts that share the same Twitch login name
   - `idpLinks[].userName` and `idpInformation.userName` — Twitch login name
7. Returns the modified response object.

---

## 5. Expected behaviour

### New user — no existing Zitadel account

1. User clicks "Login with Twitch" (or Google).
2. External provider authenticates the user and redirects back.
3. For Twitch: the normalizer enriches the `createUser` payload.
4. Zitadel creates a new account automatically. No "Complete your data" form
   is shown.
5. The user is logged in.

### Existing local user with matching verified email

1. User clicks "Login with Twitch" (or Google).
2. For Twitch: the normalizer enriches the payload.
3. Zitadel's automatic email linking finds the existing local account and attaches
   the external identity to it instead of creating a new user.
4. The user is logged in. **Instance** → **Users** → the account now shows the
   external identity under **Identity Providers**.

### Subsequent logins after linking

1. User clicks "Login with Twitch" (or Google).
2. Zitadel resolves the external identity directly to the linked account.
3. For Twitch: the normalizer receives a response with no `createUser` field and
   returns it unchanged.
4. The user is logged in immediately.

---

## 6. Validation

Watch the normalizer output during a Twitch login:

```bash
docker compose logs -f twitch-normalizer
```

A successful first-time login (new user created):

```text
[twitch-normalizer] normalized Twitch user='YourLogin' zitadel_username='twitch-123456789' email_present=True idp_id='...'
```

A login where the account was already linked (no creation needed):

```text
[twitch-normalizer] Twitch identity already resolved to an existing ZITADEL user; zitadel_user_id='...'
```

A non-Twitch IdP login (e.g. Google — action fires but normalizer skips it):

```text
[twitch-normalizer] skipping non-Twitch IdP id='...'
```
