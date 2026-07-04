backend_dir := "backend"
frontend_dir := "frontend"

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

# Initializes direnv by allowing the root, backend, and frontend directories, and adds the direnv shell hook to your shell config if not already present.
init-direnv:
    #!/usr/bin/env bash
    set -euo pipefail
    direnv allow
    (cd {{ backend_dir }} && direnv allow)
    (cd {{ frontend_dir }} && direnv allow)
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

# Initializes the development environment by resetting the database, running migrations, and seeding it with development data.
init-dev: backend-init frontend-init gen-types backend-db-reset-dev

# Initializes the ci enviroment
init-ci: backend-init frontend-init

# Runs both the backend and the frontend applications in the background, with hot-reloading enabled for development.
[parallel]
run: backend-run frontend-run

# Generates Open API from backend and then Frontend Types.
gen-types: backend-generate-types frontend-generate-types

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

# Runs frontend application
frontend-run:
    pnpm --dir {{ frontend_dir }} dev

# Initializes the frontend workspace
frontend-init:
    pnpm --dir {{ frontend_dir }} install

# Generate Frontend types from OpenAPI
frontend-generate-types:
    cd {{ frontend_dir }} && node scripts/gen-types.ts -i ../generated/api.json -o src/generated

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

# Runs the backend application using Uvicorn, with hot-reloading enabled for development.
backend-run:
    uv run --directory {{ backend_dir }} uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# Initializes the backend workspace
backend-init:
    uv sync --directory {{ backend_dir }} --dev

# Generate OpenAPI from backend.
backend-generate-types:
    uv run --directory {{ backend_dir }}  scripts/dump-fast-api.py -o ../generated/api.json

#
# Database
#

# Resets the database by stopping the postgres service, removing its volume, and starting it again.
db-reset:
    docker compose down -v postgres
    docker compose up -d --wait postgres
