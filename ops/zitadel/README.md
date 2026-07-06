# ops/zitadel — Self-hosted Zitadel IAM Stack

## Overview

This directory contains the Docker Compose stack for [Zitadel](https://zitadel.com/), the identity and access management (IAM) service for the test-conf.de platform.

Zitadel provides OIDC/OAuth2 authentication for the main website and protects the staging environment via oauth2-proxy.

**Public URL:** `https://id.test-conf.de/`

---

## Architecture

```text
Public Internet
      │
      │ HTTPS (port 443)
      ▼
Plesk nginx  ← manages TLS certificates for id.test-conf.de
      │
      │ plain HTTP (127.0.0.1:18080)
      ▼
Traefik (internal, Docker)
      │
      ├─ /ui/v2/login/*  →  zitadel-login (Next.js, port 3000)
      └─ everything else →  zitadel-api   (Zitadel, port 8080, h2c)
                                 │
                                 ▼
                            PostgreSQL (port 5432, Docker-internal only)
```

Key points:

- **Plesk** owns the public 80/443 ports and terminates TLS for `id.test-conf.de`.
- **Traefik** is the internal HTTP router, bound to `127.0.0.1:18080` only.
- **Zitadel** is configured to know it is externally reachable via HTTPS on port 443, even though Traefik receives plain HTTP from Plesk.
- The inner `websecure` (port 443) Traefik entrypoint exists in the config but is not published to the host and is not used in this deployment.
- No ports other than `127.0.0.1:18080` are exposed from this stack.

---

## Files

| File | Committed? | Purpose |
|------|------------|---------|
| `compose.yml` | ✅ Yes | Docker Compose service definitions |
| `.env.example` | ✅ Yes | Template with safe placeholders — **no real secrets** |
| `.env` | ❌ No (Git-ignored) | Private config with real secrets |
| `.gitignore` | ✅ Yes | Ensures `.env` is never committed |
| `README.md` | ✅ Yes | This file |

> **Never commit `.env`.**
> The root `.gitignore` already ignores `**/.env`; this directory also has its own
> `.gitignore` as an additional safety net.

---

## Prerequisites

- Docker and Docker Compose v2 installed on the server.
- Plesk managing a domain entry for `id.test-conf.de` pointing to this server.
- A TLS certificate for `id.test-conf.de` (managed by Plesk / Let's Encrypt).

---

## First-time Setup

### 1. Create `.env`

```bash
cp ops/zitadel/.env.example ops/zitadel/.env
```

Edit `.env` and replace all `CHANGE_ME_*` placeholders:

- **`ZITADEL_MASTERKEY`** — generate with:
  ```bash
  python3 -c "import secrets,string; print(''.join(secrets.choice(string.ascii_letters+string.digits) for _ in range(32)))"
  ```
  Must be **exactly 32 characters**. Back it up immediately (see [Backup](#backup)).

- **`POSTGRES_ADMIN_PASSWORD`** — generate with:
  ```bash
  python3 -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- **`ZITADEL_DATABASE_POSTGRES_DSN`** — update the password in the DSN to match
  `POSTGRES_ADMIN_PASSWORD`.

- **`LETSENCRYPT_EMAIL`** — set to your ops email (not used for TLS in the Plesk
  setup, but kept for reference).

All other domain/scheme/port values are already set for the `id.test-conf.de`
production deployment in `.env.example`.

### 2. Configure Plesk

In Plesk, add a reverse proxy for the `id.test-conf.de` subdomain:

- **Proxy target:** `http://127.0.0.1:18080`
- Enable **"Upgrade Insecure Requests"** / pass `X-Forwarded-Proto: https` header.
- Ensure the TLS certificate (Let's Encrypt or manual) is active.

The nginx vhost config should include something like:

```nginx
location / {
    proxy_pass         http://127.0.0.1:18080;
    proxy_set_header   Host              $host;
    proxy_set_header   X-Real-IP         $remote_addr;
    proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header   X-Forwarded-Proto https;
    proxy_http_version 1.1;
    proxy_set_header   Upgrade    $http_upgrade;
    proxy_set_header   Connection $connection_upgrade;
}
```

### 3. Start the stack

```bash
cd ops/zitadel
docker compose up -d --wait
```

The `--wait` flag blocks until all services pass their health checks.
Initial startup (`start-from-init`) may take ~60 seconds while Zitadel initialises
the database schema.

---

## Upgrading

To upgrade to a new Zitadel version:

1. Update `ZITADEL_VERSION` in `.env` (and `.env.example` if it is a stable release).
2. Pull new images and restart:
   ```bash
   cd ops/zitadel
   docker compose pull
   docker compose up -d --wait
   ```

Always pin versions — do **not** use floating tags like `latest` in production.

---

## Health Checks

Check all containers are healthy:

```bash
cd ops/zitadel
docker compose ps
```

All three services (`proxy`, `zitadel-api`, `zitadel-login`) should show `healthy`.

Check Zitadel's readiness endpoint directly (bypasses Traefik):

```bash
docker compose exec zitadel-api /app/zitadel ready
```

Check through Traefik (from the host):

```bash
curl -sf http://127.0.0.1:18080/healthz && echo OK
```

Check the public endpoint:

```bash
curl -sf https://id.test-conf.de/healthz && echo OK
```

View logs:

```bash
docker compose logs -f zitadel-api
docker compose logs -f zitadel-login
docker compose logs -f proxy
```

---

## OIDC Applications to Create

After the first successful startup, log into the Zitadel admin UI at
`https://id.test-conf.de/ui/v2/login` and create the following OIDC applications
in a dedicated project:

| App name | Environment | Notes |
|----------|-------------|-------|
| `website-dev` | Development | Website login flow, dev environment |
| `website-staging` | Staging | Website login flow, staging environment |
| `website-prod` | Production | Website login flow, production environment |
| `staging-gate` | Staging | Used by oauth2-proxy protecting `https://staging.test-conf.de/` |

For `staging-gate` (oauth2-proxy), use application type **Web** with the
[Code flow + PKCE](https://zitadel.com/docs/guides/integrate/login/oidc/oauth-recommended-flows).

For the website apps, use the flow appropriate to the frontend framework (SvelteKit
typically uses Code flow with PKCE).

---

## Backup

**What to back up:**

| Item | Why |
|------|-----|
| `ZITADEL_MASTERKEY` from `.env` | Encrypts all Zitadel data. Loss = unrecoverable instance. |
| `postgres-data` Docker volume | All Zitadel state: users, apps, sessions, tokens. |
| `.env` file (or its secrets) | Reproducibility. Store encrypted (e.g. in a vault). |

**Back up the Postgres volume:**

```bash
# While the stack is running (online backup):
docker run --rm \
  --volumes-from $(docker compose -f ops/zitadel/compose.yml ps -q postgres) \
  -v /path/to/backup:/backup \
  postgres:17.2-alpine \
  pg_dump -U postgres -d zitadel > /path/to/backup/zitadel-$(date +%Y%m%d%H%M%S).sql

# Or dump directly:
cd ops/zitadel
docker compose exec postgres pg_dump -U postgres -d zitadel > /path/to/backup/zitadel.sql
```

**Restore:**

```bash
cd ops/zitadel
docker compose exec -T postgres psql -U postgres -d zitadel < /path/to/backup/zitadel.sql
```

---

## Security Notes

- **Never rotate `ZITADEL_MASTERKEY` casually.** If you must rotate it, follow the
  official process: https://zitadel.com/docs/self-hosting/manage/updating_scaling
- **Never commit `.env`.**
- The Traefik port is bound to `127.0.0.1` only — the Zitadel stack is not directly
  reachable from the internet.
- Port 443 (Traefik's `websecure` entrypoint) is not published to the host.
- PostgreSQL is not exposed outside the `zitadel` Docker network.

---

## Relation to the Main Website

The main website (`compose.yaml`, `compose.dev.yaml`, `compose.staging.yaml`) does
**not** include Zitadel — it is a separate infrastructure stack.

The website frontend and backend will integrate with Zitadel via standard OIDC,
using the client credentials created in the [OIDC Applications](#oidc-applications-to-create)
section above.

The `ops/oauth2-proxy.compose.yaml` staging gate also integrates with Zitadel via
the `staging-gate` OIDC application.

This stack should be started and healthy before deploying the website for the first
time with auth enabled.
