# Structured Logging

This project uses structured, JSONL-formatted logs in both the Python backend and TypeScript/SvelteKit frontend. The log event schema is defined once in TypeSpec and code-generated into typed Pydantic models (Python) and Zod schemas (TypeScript).

---

## Architecture Overview

```text
logging-schema/main.tsp        ← single source of truth (TypeSpec)
         │
         ▼  just gen-log-models  (TypeSpec compilation)
$TMPDIR/…/*.json               ← JSON Schema intermediate files (temp dir, auto-cleaned)
         │
         ▼  just gen-log-models  (codegen)
backend/src/backend/logging/events_gen.py   ← Pydantic v2 models
frontend/src/logging/events.gen.ts          ← Zod schemas + factory functions
```

`just gen-log-schema` writes the JSON schema intermediate files to `logging-schema/schema/` and is available for manually inspecting the output.

In the CI, the code-gen is also invoked and the results are compared against the checked-in versions. CI signals failure if both versions differ.

---

## Log Record Format

Every record is a single-line JSON object (JSONL) written to `stdout` and optionally to a file. The format is aligned with OpenTelemetry log data model:

```json
{
  "timestamp": "2025-01-15T10:30:00.000000+00:00",
  "severity_text": "INFO",
  "body": "HTTP request completed",
  "event.name": "http.request.completed",
  "attributes": {
    "method": "GET",
    "path": "/api/v1/events",
    "status_code": 200,
    "duration_ms": 12.5,
    "request_id": "abc123"
  },
  "trace_id": null,
  "span_id": null
}
```

Severity levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.

---

## Using the Logging Façade

### Python (backend)

```python
from backend.logging import info
from backend.logging.events_gen import HttpRequestCompleted

info(HttpRequestCompleted(method="GET", path="/api/v1/events", status_code=200, duration_ms=12.5))
```

All log functions (`debug`, `info`, `warning`, `error`, `critical`) accept a single `LogEventBase` instance. Logs always go to `stdout`; they also go to the file specified by the environment variable named `LOG_FILE` (if it exists).

### TypeScript (SvelteKit server)

```typescript
import { logger } from '$logging';
import { httpRequestCompleted } from '$logging/events.gen';

logger.info(httpRequestCompleted({ method: 'GET', path: '/api/v1/events', status_code: 200, duration_ms: 12.5 }));
```

The TypeScript façade is server-only (`$lib/server/`). Factory functions validate their arguments with Zod at runtime. Logs always go to `stdout`; `LOG_FILE` routes them to a file in addition (if set).

---

## Environment Variable: `LOG_FILE`

| Value                 | Effect                                  |
|-----------------------|-----------------------------------------|
| unset / empty         | Logs to `stdout` only.                  |
| `.logs/backend.jsonl` | Logs to stdout **and** that file.       |

In development, `just backend-run` sets `LOG_FILE=.logs/backend.jsonl` and `just frontend-run` sets `LOG_FILE=.logs/frontend.jsonl`. Alloy tails these files and ships logs to Loki.

The empty `.logs/` directory is tracked by `git` via a `.gitkeep` file inside. The actual log files themselves are not tracked, however. `just init-dev` (and `just clean-logs`) removes it at session start.

---

## Local Observability Stack (Development)

The dev Compose stack includes Grafana + Loki + Grafana Alloy:

```bash
docker compose -f compose.dev.yaml up -d
```

- **Grafana**: <http://localhost:3001> — anonymous admin access in dev
- **Loki**: internal at `http://loki:3100`
- **Alloy**: tails `.logs/backend.jsonl`, `.logs/frontend.jsonl`, and Docker container logs

Alloy extracts `event_name` and `severity_text` as Loki structured metadata for efficient filtering without blowing up the label cardinality.

---

## Central Observability (Staging / Production)

A persistent Grafana+Loki instance runs at `https://logs.test-conf.de`. Access is protected by Zitadel via oauth2-proxy; users must be in the `staging-access` group.

Alloy runs alongside each deployment (`alloy.staging.compose.yaml`, `alloy.production.compose.yaml`) and ships Docker container logs to the central Loki instance via `LOKI_URL`.

Log retention: **90 days**.

---

## Adding or Changing Log Events

1. **Edit** `logging-schema/main.tsp`—add or modify a TypeSpec model.
2. **Regenerate** typed models (automatically generates the intermediate JSON schema files):

   ```bash
   just gen-log-models
   ```

3. **Commit** the two changed/added files:
   - `backend/src/backend/logging/events_gen.py`
   - `frontend/src/logging/events.gen.ts`

The CI job `validate-generated-log-models` will fail if the committed files don’t match what would be generated from `main.tsp`.

---

## CI Validation

`.github/workflows/validate-generated-log-models.yml` runs on every pull request. It runs `just gen-log-models` and checks `git diff --exit-code` on both generated files.

This ensures the committed generated files are never stale.

---

## Security / Privacy Notes

- **Never log Personally Identifiable Information (PII)** (names, emails, IP addresses) in structured attributes. Use opaque IDs and aggregate statistics.
- Log files in `.logs/` are local to the developer’s machine and are not committed.
- The central Loki instance is access-controlled via OAuth2; only authenticated members of the `staging-access` group can view logs.
- Loki labels are low-cardinality (`service_name`, `environment`). High-cardinality values go in structured metadata or log body, never in labels.

---

## External Logs (nginx, PostgreSQL)

Nginx is configured with a structured `json_access` log format (`ops/nginx/nginx.conf`). These logs appear in Docker `stdout` and are picked up by Alloy’s Docker discovery component alongside application logs.

PostgreSQL logs are also captured via Docker `stdout` discovery.
