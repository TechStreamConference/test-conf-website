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

# Runs formatters, linters, and type checkers on both the backend and the frontend codebases, applying automatic fixes where possible.
fix: backend-fix frontend-fix

# Runs both the backend and the frontend test suites, measuring code coverage.
test: backend-test frontend-test

# Initializes the development environment by resetting the database, running migrations, and seeding it with development data.
init-dev: backend-init backend-db-reset-dev frontend-init

# Runs both the backend and the frontend applications in the background, with hot-reloading enabled for development.
run: backend-run frontend-run


#
# Frontend
#

# Runs the formatter, linter, and type checker on the frontend codebase, applying automatic fixes where possible.
frontend-fix:
    @echo "TODO: FRONTEND FIX"

# Runs the test suite for the frontend codebase, measuring code coverage.
frontend-test:
    @echo "TODO: FRONTEND TEST"

# Runs frontend application
frontend-run:
    @echo "TODO: FRONTEND RUN"

# Initializes the frontend workspace
frontend-init:
    cd {{frontend_dir}}
    pnpm install

#
# Backend
#

# Runs the database migrations using Alembic.
backend-migrate:
    uv run --directory {{backend_dir}} alembic upgrade head

# Creates a new Alembic migration with the given message.
backend-migration message:
    uv run --directory {{backend_dir}} alembic revision --autogenerate -m "{{message}}"

# Seeds the database with production data.
backend-seed-prod:
    uv run --directory {{backend_dir}} -m backend.seed.cli prod

# Seeds the database with development data.
backend-seed-dev num-users="10" seed="12345":
    uv run --directory {{backend_dir}} -m backend.seed.cli dev --num-users {{num-users}} --seed {{seed}}

# Resets the database, runs migrations, and seeds the database with development data.
backend-db-reset-dev num-users="10" seed="12345": db-reset backend-migrate (backend-seed-dev num-users seed)

# Runs the formatter, linter, and type checker on the backend codebase, applying automatic fixes where possible.
backend-fix:
    uv run --directory {{backend_dir}} poe fix

# Runs the test suite for the backend codebase, measuring code coverage.
backend-test:
    uv run --directory {{backend_dir}} poe test

# Runs the backend application using Uvicorn, with hot-reloading enabled for development.
backend-run:
    uv run --directory {{backend_dir}} uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

# Initializes the backend workspace
backend-init:
    uv sync --directory {{backend_dir}} --dev

#
# Database
#

# Resets the database by stopping the postgres service, removing its volume, and starting it again.
db-reset:
    docker compose down -v postgres
    docker compose up -d --wait postgres
