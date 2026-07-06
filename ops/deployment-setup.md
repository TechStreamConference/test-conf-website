# Deployment Setup Guide

This document describes how to wire up automated deployment for a new environment
(staging is already done; follow these steps when setting up production or any
future environment).

The deployment flow is:

1. A PR is merged into `main` (or the workflow is triggered manually).
2. GitHub Actions builds the backend and frontend Docker images and pushes them to
   GitHub Container Registry (GHCR).
3. GitHub Actions SSHes into the target server as a restricted deploy user.
4. The SSH connection runs a forced-command script that pulls the new images and
   restarts the Compose stack.

### Image tagging strategy

Each environment gets its own mutable tag so images are never mixed up:

| Environment | Mutable tag pushed by CI | Image reference in Compose |
|-------------|--------------------------|----------------------------|
| staging     | `:staging`               | `backend:${ENVIRONMENT}`   |
| prod        | `:prod`                  | `backend:${ENVIRONMENT}`   |

Every build also pushes an **immutable commit-SHA tag** (e.g. `:abc1234f`) in
addition to the environment tag. This provides a full audit trail and allows
rolling back to any previous build by retagging without a rebuild.

The `${ENVIRONMENT}` variable is already used throughout the Compose files, so
no changes are needed in the service definitions when adding a new environment —
only the CI workflow needs a new build/deploy job.

---

## 1. Repository changes

### 1.1 Nginx config

Create `ops/nginx/<env>/default.conf` for the new environment. Copy the staging
config as a starting point and adjust:

- `server_name` — the public domain for this environment
- `proxy_pass` URLs — service names stay the same (`oauth2-proxy`, `frontend`,
  `backend`); they are resolved via Docker's internal DNS
- `--redirect-url` in `ops/oauth2-proxy.compose.yaml` if a separate
  oauth2-proxy instance is used

### 1.2 Nginx Compose file

Create `ops/nginx.<env>.compose.yaml`. Copy `ops/nginx.staging.compose.yaml` and
change:

- `container_name` — the `${ENVIRONMENT}` variable handles this automatically
- `ports` — pick a **unique local port** for nginx on this server:

  | Environment | Port  |
  |-------------|-------|
  | staging     | 18082 |
  | prod        | 18083 |

  The port only needs to be unique on the host; it is bound to `127.0.0.1` only
  and is never exposed publicly.

### 1.3 Environment Compose file

Create `compose.<env>.yaml` and list all included service files for this
environment (see `compose.staging.yaml` as the reference).

### 1.4 Deploy script

Create `ops/deploy-<env>.sh` (copy `ops/deploy-staging.sh` and adapt):

- Update the `cd` path to match the deployment directory on the server.
- Set `ENVIRONMENT=<env>`.

Make it executable:

```bash
chmod +x ops/deploy-<env>.sh
```

### 1.5 GitHub Actions workflow

Add build and deploy jobs for the new environment to
`.github/workflows/deploy.yml`. The build jobs are the same; only the trigger
condition and the SSH secrets differ per environment. Production deployments
should not run automatically on every push to `main` — restrict them to
`workflow_dispatch` or a release event.

---

## 2. Server setup

All commands below are run **on the server as root**.

### 2.1 Create the deploy user

Follow the naming convention `deploy-<project>-<env>`:

```bash
sudo useradd --system --create-home --shell /bin/bash deploy-test-conf-<env>
sudo mkdir -p /home/deploy-test-conf-<env>/.ssh
sudo chmod 700 /home/deploy-test-conf-<env>/.ssh
sudo chown deploy-test-conf-<env>:deploy-test-conf-<env> \
    /home/deploy-test-conf-<env>/.ssh
```

### 2.2 Add the user to required groups

```bash
# Allow the user to run Docker commands
sudo usermod -aG docker deploy-test-conf-<env>

# Allow the user to traverse the Plesk vhosts directory
# (the parent dir /var/www/vhosts/test-conf.de/ has group psaserv with +x)
sudo usermod -aG psaserv deploy-test-conf-<env>
```

### 2.3 Create and own the deployment directory

```bash
sudo mkdir -p /var/www/vhosts/test-conf.de/<env>.test-conf.de
sudo chown -R deploy-test-conf-<env>:deploy-test-conf-<env> \
    /var/www/vhosts/test-conf.de/<env>.test-conf.de
```

### 2.4 Clone the repository into the deployment directory

```bash
sudo -u deploy-test-conf-<env> git clone \
    git@github.com:TechStreamConference/test-conf-website.git \
    /var/www/vhosts/test-conf.de/<env>.test-conf.de
```

### 2.5 Install the deploy script

```bash
sudo cp /var/www/vhosts/test-conf.de/<env>.test-conf.de/ops/deploy-<env>.sh \
    /usr/local/bin/deploy-test-conf-<env>.sh
sudo chmod +x /usr/local/bin/deploy-test-conf-<env>.sh
```

Verify the `cd` path inside the script matches the deployment directory.

### 2.6 Create the `.env` file

Copy `.env.example` and fill in all values:

```bash
cp /var/www/vhosts/test-conf.de/<env>.test-conf.de/.env.example \
   /var/www/vhosts/test-conf.de/<env>.test-conf.de/.env
```

Required variables that are not pre-filled:

| Variable | How to obtain |
|----------|---------------|
| `ENVIRONMENT` | Set to `<env>` (e.g. `staging`, `prod`) |
| `DATABASE_PASSWORD` | Generate: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `OAUTH2_PROXY_CLIENT_ID` | From the Zitadel application registration |
| `OAUTH2_PROXY_CLIENT_SECRET` | From the Zitadel application registration |
| `OAUTH2_PROXY_COOKIE_SECRET` | Generate: `python3 -c "import secrets, base64; print(base64.urlsafe_b64encode(secrets.token_bytes(32)).decode())"` |

---

## 3. SSH key setup

### 3.1 Generate a dedicated key pair

Run this **locally** (not on the server):

```bash
ssh-keygen -t ed25519 \
    -C "github-actions-deploy-test-conf-<env>" \
    -f deploy-test-conf-<env> \
    -N ""
```

This creates:

- `deploy-test-conf-<env>` — **private key** → paste as the GitHub secret
  `<ENV>_DEPLOY_SSH_KEY` (see §4)
- `deploy-test-conf-<env>.pub` — **public key** → install on the server in §3.2

### 3.2 Install the public key with a forced command

Replace `<public-key-contents>` with the single line from the `.pub` file:

```bash
echo 'command="/usr/local/bin/deploy-test-conf-<env>.sh",no-port-forwarding,no-agent-forwarding,no-pty <public-key-contents>' \
    | sudo tee /home/deploy-test-conf-<env>/.ssh/authorized_keys

sudo chmod 600 /home/deploy-test-conf-<env>/.ssh/authorized_keys
sudo chown deploy-test-conf-<env>:deploy-test-conf-<env> \
    /home/deploy-test-conf-<env>/.ssh/authorized_keys
```

The forced command means the deploy user can **only** trigger the deploy script
and cannot open an interactive shell, regardless of what the SSH client requests.

### 3.3 Test the SSH connection

```bash
ssh -i deploy-test-conf-<env> deploy-test-conf-<env>@<server-hostname>
```

The connection should run the deploy script and exit. The message
`PTY allocation request failed on channel 0` is expected and harmless — it is
the server rejecting a terminal because of `no-pty` in `authorized_keys`.

---

## 4. GitHub secrets

Go to: **Repository → Settings → Secrets and variables → Actions → New
repository secret**

| Secret name | Value |
|-------------|-------|
| `<ENV>_DEPLOY_HOST` | Server hostname or IP (e.g. `staging.test-conf.de`) — **no** `https://` prefix |
| `<ENV>_DEPLOY_USER` | `deploy-test-conf-<env>` |
| `<ENV>_DEPLOY_SSH_KEY` | Full contents of the private key file generated in §3.1 |

`GITHUB_TOKEN` is provided automatically by GitHub Actions; no action needed.

---

## 5. Plesk setup

In Plesk, configure a **reverse proxy** (not a Docker proxy rule) for
`<env>.test-conf.de`:

- **Proxy URL:** `http://127.0.0.1:<nginx-port>` (see port table in §1.2)

Plesk terminates TLS (HTTPS on 443) and forwards plain HTTP to nginx on the
local port. The `X-Forwarded-Proto: https` header is set by Plesk's nginx so
that oauth2-proxy sets `secure` cookies correctly.

---

## 6. First-time image publication

GHCR packages are **private by default** when first pushed. After the first
successful workflow run (or a manual push), make each package public:

1. Go to `https://github.com/orgs/TechStreamConference/packages`
2. Open `test-conf-website/backend` → **Package settings** → Change visibility →
   **Public**
3. Repeat for `test-conf-website/frontend`

This only needs to be done once per package; subsequent pushes keep the existing
visibility setting.

---

## 7. Verification checklist

- [ ] `ssh -i deploy-test-conf-<env> deploy-test-conf-<env>@<host>` runs the
      deploy script and exits cleanly
- [ ] `curl -si http://127.0.0.1:<nginx-port>/` returns an HTTP response from
      inside the server
- [ ] `https://<env>.test-conf.de/` redirects to Zitadel login
- [ ] After login, the frontend is served correctly
- [ ] `https://<env>.test-conf.de/api/health/database` returns `{"ok": true}`
- [ ] Merging a PR into `main` triggers the workflow and the running containers
      are updated automatically
