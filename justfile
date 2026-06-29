backend_dir := "backend"

default:
    @just --list

up:
    docker compose up -d --wait

down:
    docker compose down

db-reset:
    docker compose down -v postgres
    docker compose up -d --wait postgres

backend-migrate:
    uv run --directory {{backend_dir}} alembic upgrade head

backend-migration message:
    uv run --directory {{backend_dir}} alembic revision --autogenerate -m "{{message}}"

backend-seed-prod:
    uv run --directory {{backend_dir}} -m backend.seed.cli prod

backend-seed-dev num-users="10" seed="12345":
    uv run --directory {{backend_dir}} -m backend.seed.cli dev --num-users {{num-users}} --seed {{seed}}

backend-db-reset-dev num-users="10" seed="12345": db-reset backend-migrate (backend-seed-dev num-users seed)

backend-fix:
    uv run --directory {{backend_dir}} poe fix

backend-test:
    uv run --directory {{backend_dir}} poe test

backend-run:
    uv run --directory {{backend_dir}} uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload

fix: backend-fix

test: backend-test

init-dev: backend-db-reset-dev

run: backend-run
