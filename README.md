# TECH STREAM CONFERENCE WEBSITE

## Setup

### 1. Install Nix (one-time)

```sh
curl --proto '=https' --tlsv1.2 -fsSL https://install.determinate.systems/nix | sh -s -- install
```

This uses the recommended [Determinate Systems installer](https://install.determinate.systems). You can use another installation method, but make sure your Nix version supports flakes.

### 2. Clone the Repository

```sh
git clone git@github.com:TechStreamConference/test-conf-website.git
cd test-conf-website
```

You can also use the HTTPS URL from the [repository page](https://github.com/TechStreamConference/test-conf-website).

### 3. Enter a Development Shell

```sh
nix develop
```

### 4. Install dependencies

Run `just setup` from the relevant directory:

| Directory    | Effect                             |
|--------------|------------------------------------|
| `./`         | Sets up all dependencies           |
| `backend/`   | Sets up only backend dependencies  |
| `frontend/`  | Sets up only frontend dependencies |

```sh
just setup
```

### Storybook

Start the local component playground from the repository root:

```sh
just storybook
```

Storybook is then available at [http://localhost:6006](http://localhost:6006).

---

### Optional: Automatic shell activation with direnv

[direnv](https://direnv.net) is optional but recommended. It automatically loads the correct Nix development shell when you enter the repository or any of its subdirectories, so you do not need to run `nix develop` manually.

**direnv must be installed on your system outside of the project’s Nix shell.** Follow the [direnv installation guide](https://direnv.net/docs/installation.html) and hook it into your shell.

If you use VS Code, also install a direnv extension (e.g. [mkhl.direnv](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv)).

The repository includes a single `.envrc` at the root:

```envrc
use flake
```

Run `just init-direnv` to allow it and add the direnv shell hook to your shell config. Because `just` is provided by the Nix shell, enter it manually the first time:

```sh
nix develop       # Enter Nix shell.
just init-direnv  # Setup direnv.
```

After that, direnv will activate the shell automatically whenever you enter the repository.

If you prefer not to use direnv, you can always enter the shell manually with `nix develop`.

---

## Logging

Both the backend and the frontend emit structured JSON log records (JSONL format). The schema is defined once in TypeSpec and code-generated into
typed models for both languages—see [docs/logging.md](docs/logging.md) for the full architecture.

### Local development

`just run` starts both services. Because `ENVIRONMENT=dev` is set in `.env`, logs are printed to the terminal in a human-readable, syntax-highlighted format:

```text
[backend] INFO     application.started
{
  "timestamp": "2026-08-17T10:00:00.000000+00:00",
  "severity_text": "INFO",
  ...
}
```

Each service also writes raw JSONL to a spool file that Alloy tails:

| Service  | Spool file                  |
|----------|-----------------------------|
| backend  | `.logs/backend.jsonl`       |
| frontend | `.logs/frontend.jsonl`      |

You can inspect these files directly with `tail -f .logs/backend.jsonl`.

The full observability stack (Alloy → Loki → Grafana) is part of the default dev Compose stack and starts automatically with `just up`:

```sh
just up      # starts nginx, postgres, loki, alloy, grafana
just run     # starts backend + frontend
```

**Grafana (dev):** <http://localhost:3001> — no login required.

Open the *Explore* view, select the *Loki* data source, and filter by label. Then click “Run Query”.

### Staging and production

A shared Grafana + Loki instance is running at <https://logs.test-conf.de>.

Access requires a Zitadel account that is a member of the `staging-access` group. Contact a project admin if you need access.

Use the same Explore / LogQL workflow as in dev. To filter by environment.

### Adding or changing log events

1. Edit `logging-schema/main.tsp`.
2. Run `just gen-log-models`.
3. Commit the updated schema JSON files and the generated `events_gen.py` / `events.gen.ts`.

See [docs/logging.md](docs/logging.md) for the detailed workflow and CI validation.
