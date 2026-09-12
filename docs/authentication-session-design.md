# Authentication and Session Design

Tech Stream Conference website · FastAPI + SvelteKit + ZITADEL

## Scope

This document defines login, local user creation, application sessions, logout, and CSRF protection.

- **ZITADEL** authenticates users.
- **FastAPI** owns OIDC, application sessions, local users, roles, and authorization.
- **SvelteKit** only forwards frontend requests to FastAPI and has no database access.

## 1. Decisions

| Item | Decision |
| --- | --- |
| OIDC client | FastAPI. Use Authlib and OIDC Authorization Code Flow with PKCE. |
| Identity provider | ZITADEL. Login may use username/password, Google, or Twitch. |
| Local identity key | Use an internal user primary key plus a unique ZITADEL subject/user ID. Do not identify users by email or username. |
| Application session | Opaque random session token in an HttpOnly cookie. Store only its SHA-256 hash in PostgreSQL. |
| OIDC tokens | Use them only during login. Do not store or validate a ZITADEL JWT on every normal request. |
| Logout | Invalidate the local session and also perform ZITADEL RP-initiated logout. |

## 2. Architecture

```text
Browser -> SvelteKit -> FastAPI -> PostgreSQL
                         |
                         +-> ZITADEL (OIDC only)
```

SvelteKit forwards requests and responses. It must preserve cookies, query parameters, `Origin`, `Set-Cookie`, `Location`, and redirect status codes.

ZITADEL is contacted during login and logout, not for every application request.

## 3. Login flow

1. The browser requests `GET /auth/login`, optionally with a validated local return path.
2. FastAPI creates a short-lived OIDC login transaction containing:
   - `state`
   - `nonce`
   - PKCE code verifier
   - browser-binding secret
   - return path
   - expiry
3. FastAPI stores the transaction server-side and sets a short-lived HttpOnly login cookie containing only the browser-binding secret.
4. FastAPI redirects the browser to ZITADEL.
5. ZITADEL authenticates or registers the user and redirects to `GET /auth/callback?code=...&state=...`.
6. FastAPI verifies and consumes the login transaction. Authlib exchanges the code and validates the OIDC response and ID token.
7. FastAPI reads the stable ZITADEL subject (`sub`), email, preferred username, and `sid` when available.
8. FastAPI finds the local user by ZITADEL subject. If none exists, it creates a user row with the default local role/state. Mutable profile fields may be synchronized.
9. FastAPI creates an application session, sets the application session cookie, removes the temporary login cookie, and redirects to the validated return path.

## 4. Data model

```text
users
  id                  PK (internal application ID)
  zitadel_user_id     UNIQUE NOT NULL   # OIDC sub
  email
  username
  ... local roles / account data

sessions
  id                  PK
  user_id             FK -> users.id
  token_hash          UNIQUE NOT NULL   # SHA-256(session token)
  zitadel_session_id  NULLABLE          # OIDC sid; used later for back-channel logout
  created_at
  last_seen_at
  expires_at
  absolute_expires_at
  revoked_at          NULLABLE

oidc_login_transactions
  state_hash          PK                # SHA-256(state), lowercase hex
  browser_secret_hash NOT NULL          # SHA-256(browser-binding secret)
  nonce               NOT NULL          # raw; validated against the ID token claim
  pkce_code_verifier  NOT NULL          # raw; sent verbatim to the token endpoint
  return_to           NOT NULL
  created_at          NOT NULL
  expires_at          NOT NULL
```

The internal user ID keeps application foreign keys independent from ZITADEL. A future ZITADEL migration or identity-provider change must not require changing all related rows.

## 5. Application sessions

- Generate the session token with a cryptographically secure RNG. Use at least 256 random bits.
- Store only `SHA-256(session_token)`. The raw token is a bearer credential, so a database leak alone must not expose usable sessions.
- The database is authoritative. An expired or revoked database session is invalid even if the browser still has the cookie.
- Use sliding idle expiry. Recommended initial values:
  - idle timeout: **30 days**
  - absolute lifetime: **90 days**
- Keep both values configurable.
- Refresh `last_seen_at`, `expires_at`, and the cookie periodically rather than on every request, for example once per hour.
- When the absolute lifetime is reached, run OIDC login again. An existing ZITADEL SSO session may make this nearly transparent.

### Cookie settings

```text
Name:     __Host-session
Flags:    Secure; HttpOnly; SameSite=Lax; Path=/
Domain:   do not set
```

Do not hard-bind sessions to an IP address or browser fingerprint. These values can change legitimately and create reliability and privacy problems.

IP address and User-Agent may be stored as audit signals, but should not be strict authentication requirements.

## 6. Authentication of normal requests

```text
request cookie
  -> SHA-256(token)
  -> find active, non-expired session
  -> load local user
  -> apply local authorization
```

Do **not** fetch a stored ZITADEL JWT and do **not** call ZITADEL token introspection for each request.

Authlib validates ZITADEL during the login flow. After that, the local FastAPI session is the authentication authority.

## 7. CSRF protection

Protect state-changing methods such as `POST`, `PUT`, `PATCH`, and `DELETE`.

FastAPI has no single built-in "enable CSRF" switch. Implement this with middleware/dependencies or a suitable library.

Use these protections together:

- require the expected `Origin` for browser state-changing requests;
- ensure SvelteKit preserves the `Origin` header;
- use a standard CSRF token mechanism;
- keep the application session cookie HttpOnly;
- send the CSRF value separately, for example via `X-CSRF-Token`;
- keep `SameSite=Lax` as an additional protection, not the only protection.

## 8. Logout

1. `POST /auth/logout` invalidates or revokes the local database session.
2. FastAPI expires the `__Host-session` cookie.
3. FastAPI redirects the browser to ZITADEL's OIDC end-session endpoint with a validated post-logout redirect URI and `state`.
4. ZITADEL ends its SSO session and redirects back to the site.

## 9. Initial API surface

```text
GET   /auth/login
GET   /auth/callback
POST  /auth/logout
GET   /auth/me
```

`/auth/me` returns the current local user and application roles derived from the FastAPI session. It must not expose OIDC tokens.

## 10. Implementation rules

- Use **Authlib** for OIDC. Do not implement signature checks, PKCE, nonce validation, or authorization-code exchange manually.
- Treat `return_to` as an application-local path. Reject arbitrary external redirect URLs.
- OIDC login transactions are single-use and short-lived. Recommended lifetime: **10 minutes**.
- Delete or consume login transactions after the callback.
- Clean up expired login transactions and sessions periodically.
- Use database constraints for unique ZITADEL user IDs and unique session-token hashes.
- Create the local user and initial application session safely so concurrent first logins cannot create duplicate users.

## 11. Follow-up work

- Implement ZITADEL back-channel logout using the OIDC `sid` claim. Store `sid` now, but implement the callback later.
- Optionally add a session-management UI to show and revoke active sessions.
- Optionally add anomaly detection using audit data such as IP or User-Agent changes. Do not make this part of the initial authentication decision.
