backend_dir := "backend"
frontend_dir := "frontend"
schema_dir := "logging-schema"
codegen_dir := "logging-schema/codegen"

#
# General
#

# Shows a list of available commands in this Justfile.
default:
    @just --list

# Starts the Docker Compose stack as demon process and waits for all services to be healthy.
up:
    docker compose up -d --wait

# Stops the Docker Compose stack.
down:
    docker compose down

# Runs the formatter, linter, and type checker on both the backend and the frontend codebase without making any changes, reporting issues only.
check: backend-check frontend-check

# Runs formatters, linters, and type checkers on both the backend and the frontend codebases, applying automatic fixes where possible.
fix: backend-fix frontend-fix

# Runs both the backend and the frontend test suites, measuring code coverage.
test: backend-test frontend-test

# Initializes direnv by allowing the root directory and adds the direnv shell hook to your shell config if not already present.
init-direnv:
    #!/usr/bin/env bash
    set -euo pipefail
    direnv allow
    case "$SHELL" in
        */zsh)  rc="$HOME/.zshrc";  hook='eval "$(direnv hook zsh)"'  ;;
        */bash) rc="$HOME/.bashrc"; hook='eval "$(direnv hook bash)"' ;;
        *)
            echo "Unknown shell '$SHELL'. Add the direnv hook to your shell config manually."
            exit 0
            ;;
    esac
    if grep -qF "$hook" "$rc" 2>/dev/null; then
        echo "direnv hook already present in $rc"
    else
        printf '%s\n' "$hook" >> "$rc"
        echo "Added direnv hook to $rc — open a new terminal or run: source $rc"
    fi

# Initializes the development environment: installs deps, resets DB, generates types, cleans old log spools.
init-dev: backend-init frontend-init gen-types gen-log-models backend-db-reset-dev clean-logs

# Removes old local log spool files. Called automatically at the start of a fresh development session.
clean-logs:
    rm -rf .logs

# Runs both the backend and the frontend applications in the background, with hot-reloading enabled for development.
[parallel]
run: backend-run frontend-run

# Generates Open API from backend and then Frontend Types.
[script]
gen-types:
    temp_dir=$(mktemp -d)
    trap 'rm -rf "$temp_dir"' EXIT

    uv run --directory {{ backend_dir }} scripts/dump-fast-api.py \
        -o "$temp_dir/backend/openapi.json"

    pnpm --dir {{ frontend_dir }} exec node scripts/gen-types.js \
        -i "$temp_dir/backend/openapi.json" \
        -o src/generated


# Compiles the TypeSpec log schema to JSON Schema files in logging-schema/schema/. Useful for
# inspecting the intermediate output; normal code-gen via gen-log-models uses a temp dir instead.
gen-log-schema:
    pnpm --dir {{ schema_dir }} exec tsp compile .

# Generates typed log event models (Pydantic + Zod) from the TypeSpec schema.
# Intermediate JSON Schema files are written to a temp dir and cleaned up automatically.
[script]
gen-log-models:
    temp_dir=$(mktemp -d)
    trap 'rm -rf "$temp_dir"' EXIT

    pnpm --dir {{ schema_dir }} exec tsp compile . \
        --option "@typespec/json-schema.emitter-output-dir=$temp_dir"

    uv run --directory {{ codegen_dir }} python -m codegen \
        --input "$temp_dir" \
        --python-output "{{ justfile_directory() }}/{{ backend_dir }}/src/backend/logging/events_gen.py" \
        --typescript-output "{{ justfile_directory() }}/{{ frontend_dir }}/src/logging/events.gen.ts"
    uv run --directory {{ backend_dir }} ruff format src/backend/logging/events_gen.py
    pnpm --dir {{ frontend_dir }} exec prettier --write src/logging/events.gen.ts

#
# Frontend
#

# Runs the formatter, linter, and type checker on the frontend codebase without making any changes, reporting issues only.
frontend-check:
    pnpm --dir {{ frontend_dir }} run check

# Runs the formatter, linter, and type checker on the frontend codebase, applying automatic fixes where possible.
frontend-fix:
    pnpm --dir {{ frontend_dir }} run fix

# Runs the test suite for the frontend codebase, measuring code coverage.
frontend-test:
    pnpm --dir {{ frontend_dir }} run test

# Runs the end-to-end test suite against the locally running application.
e2e-test:
    PATH="$(dirname "$(command -v node)"):/usr/bin:/bin:$PATH" pnpm --dir {{ frontend_dir }} run test:e2e

# Opens the Playwright UI for the end-to-end test suite.
e2e-ui:
    PATH="$(dirname "$(command -v node)"):/usr/bin:/bin:$PATH" pnpm --dir {{ frontend_dir }} exec playwright test --ui

# Opens the Playwright Inspector in codegen mode to interactively record a new test.
e2e-codegen url="http://localhost":
    PATH="$(dirname "$(command -v node)"):/usr/bin:/bin:$PATH" pnpm --dir {{ frontend_dir }} exec playwright codegen {{ url }}

# Installs the Playwright browsers and their system dependencies.
e2e-init:
    PATH="$(dirname "$(command -v node)"):/usr/bin:/bin:$PATH" pnpm --dir {{ frontend_dir }} exec playwright install --with-deps

# Runs the frontend application with structured log output directed to .logs/frontend.jsonl.
frontend-run:
    LOG_FILE=.logs/frontend.jsonl pnpm --dir {{ frontend_dir }} dev

# Builds and starts Storybook locally for developing UI components in isolation.
storybook: frontend-storybook-build
    pnpm --dir {{ frontend_dir }} run storybook

# Builds Storybook to verify that all component stories compile successfully.
frontend-storybook-build:
    pnpm --dir {{ frontend_dir }} run build-storybook

# Initializes the frontend workspace
frontend-init:
    pnpm --dir {{ frontend_dir }} install

#
# Backend
#

# Runs the database migrations using Alembic.
backend-migrate:
    uv run --directory {{ backend_dir }} alembic upgrade head

# Creates a new Alembic migration with the given message.
backend-migration message:
    uv run --directory {{ backend_dir }} alembic revision --autogenerate -m "{{ message }}"

# Seeds the database with production data.
backend-seed-prod:
    uv run --directory {{ backend_dir }} -m backend.seed.cli prod

# Seeds the database with development data.
backend-seed-dev num-users="10" seed="12345":
    uv run --directory {{ backend_dir }} -m backend.seed.cli dev --num-users {{ num-users }} --seed {{ seed }}

# Resets the database, runs migrations, and seeds the database with development data.
backend-db-reset-dev num-users="10" seed="12345": db-reset backend-migrate (backend-seed-dev num-users seed)

# Runs the formatter, linter, and type checker on the backend codebase without making any changes, reporting issues only.
backend-check:
    uv run --directory {{ backend_dir }} poe check

# Runs the formatter, linter, and type checker on the backend codebase, applying automatic fixes where possible.
backend-fix:
    uv run --directory {{ backend_dir }} poe fix

# Runs the test suite for the backend codebase, measuring code coverage.
backend-test:
    uv run --directory {{ backend_dir }} poe test

# Runs ruff and pyright on the codegen project.
codegen-check:
    uv run --directory {{ codegen_dir }} ruff check src/
    uv run --directory {{ codegen_dir }} pyright src/

# Runs the test suite for the codegen project.
codegen-test:
    uv run --directory {{ codegen_dir }} pytest

# Runs the backend application using Uvicorn, with structured log output directed to .logs/backend.jsonl.
backend-run:
    LOG_FILE=.logs/backend.jsonl uv run --directory {{ backend_dir }} uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# Initializes the backend workspace
backend-init:
    uv sync --directory {{ backend_dir }} --dev

#
# Database
#

# Resets the database by stopping the postgres service, removing its volume, and starting it again.
db-reset:
    docker compose down -v postgres
    docker compose up -d --wait postgres

#
# CI
#

# CI: Initializes the ci enviroment
init-ci:
    pnpm --dir {{ frontend_dir }} install --frozen-lockfile
    uv sync --directory {{ backend_dir }} --dev --locked --exact
    pnpm --dir {{ schema_dir }} install --frozen-lockfile
    uv sync --directory {{ codegen_dir }} --locked --exact
