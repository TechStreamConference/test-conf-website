# Backend contribution guidance

Follow the existing architecture and conventions before introducing new patterns.

## Architecture and dependencies

- Keep straightforward database access in the route or existing domain module. Do not introduce repository, service, or unit-of-work layers merely to wrap SQLAlchemy calls.
- Put genuinely reusable domain rules in a focused backend module rather than duplicating them across routes.
- Use FastAPI's OpenAPI document as the source of truth for frontend API types. Regenerate them with `just gen-types` from the repository root; do not edit `frontend/src/generated/` manually.
- Manage Python dependencies and the lockfile with `uv` commands such as `uv add`; do not edit tool-managed dependency entries manually.
- Configuration is loaded from the repository-root `.env`. When adding a required setting, also update the root `.env.example`, which is validated by a meta-test and inform the user of the change so that they can also edit the `.env` file (or ask them whether you should edit it for them if you have the required data).

## Python and typing

- Use modern Python syntax supported by the project's minimum Python version.
- Prefer PEP 695 `type` statements for named type aliases.
- Prefer reusable `Annotated` types with Pydantic validators when validation belongs to a semantic type rather than a specific model field.
- Use `NamedTuple` for small immutable data carriers that do not need dataclass behavior.
- Mark classes that are not intended for inheritance with `@final`.
- Do not add redundant `Final` annotations to module-level `SCREAMING_SNAKE_CASE` constants; Pyright already treats those names as constants.
- Use `Final` for local variables that are not re-assigned. Note that this is not possible inside loops.
- When trying to write long string literals that exceed the allowed maximum line length, split them across multiple lines, but *do not* use implicit concatenation. Instead, use the `+` operator.
- Only use `f`-strings if they actually use string interpolation.
- Don't treat `Optional[T]` as being semantically equal to `T | None`: `Optional[T]` means that the value might be *missing* while `T | None` means that `None` is a meaningful value of its own.
- Assign intentionally ignored non-`None` return values to `_`; Pyright's `reportUnusedCallResult` is enabled.
- Keep type-ignore comments as narrow as possible and include the specific Pyright diagnostic. Do not use blanket file-level ignores to work around untyped dependencies.
- Do not rely on type-checking-time-only checks. Guard them with real runtime type checks where possible. Therefore, avoid `cast`s unless absolutely necessary. Wrap untyped external code using typesafe wrappers where possible.

## API models

- Keep request and response contracts precise so the generated frontend client receives accurate types.
- Model fields that must be present or absent together as one nullable nested object, rather than as independently nullable fields.
- Follow the existing API-version suffix convention for generated request and response model names.
- Define request and response payloads as Pydantic models and return those models from route functions rather than ad-hoc dictionaries.
- For expected HTTP errors, define a versioned response model, document it in the route's `responses`, and raise it through `create_http_exception`.
- Until said otherwise, stay on v1 of the API, even when making breaking changes. But ensure that the frontend follows along (this is a monorepo).

## FastAPI routes

- Define module routers as `ROUTER` and include new v1 routers in `backend.routes.v1_api`.
- Use `Annotated[..., Depends(...)]` for dependencies.
- Give every versioned API endpoint an explicit summary, description where useful, status code, return annotation, and `operation_id`. Versioned API operation IDs must end in `v<digits>`.
- Every explicitly documented response must provide a response model. The route metadata and response-model naming rules are enforced in `src/test/test_meta.py`.

## Persistence and migrations

- PostgreSQL is the authoritative database. Do not design behavior around SQLite-specific semantics.
- Use the shared asynchronous SQLAlchemy session dependency and explicit transaction boundaries. Use `flush()` when a generated identifier is needed before the surrounding transaction is committed.
- Database timestamps are stored as naïve UTC values. Use `utc_now()` or the established naïve-UTC pattern unless performing an intentional schema-wide datetime redesign.
- Keep SQLModel table definitions in `backend.models.tables`, with explicit table names and `@final` on concrete table models.
- Every schema change requires an Alembic migration. Create revisions through `just backend-migration <message>` from the repository root (or the equivalent Alembic command), then review the generated operations.
- Changes to Python enums persisted as SQLAlchemy enum types require a matching migration that updates the PostgreSQL enum type.

## Authentication and security

- Preserve the separation between `User` and `Account`: users may be virtual and have no login-capable account. External identity linkage uses the unique ZITADEL subject, never email or username.
- Normal requests authenticate against the local database session. Do not persist OIDC access/ID tokens or call ZITADEL introspection on every request.
- Session and browser secrets must come from a cryptographically secure generator. Store bearer tokens only as hashes and use constant-time comparison for secrets.
- Preserve all `__Host-` cookie requirements, including on deletion: `Secure`, host-only (no `Domain`), and `Path=/`. Keep authentication cookies `HttpOnly` with the established `SameSite` policy.
- OIDC login transactions are single-use and must be consumed before validation completes so failed or replayed callbacks cannot reuse them. Keep externally visible transaction errors deliberately generic.
- Before changing login, logout, session, redirect, or CSRF behavior, read `../docs/authentication-session-design.md` and preserve its security decisions unless the task explicitly changes them.

## Logging and generated files

- Use the typed `backend.logging` façade and generated log-event models rather than Python's standard logging API or unstructured messages.
- Never log PII such as names, email addresses, or IP addresses. Prefer opaque identifiers and aggregate values.
- `../logging-schema/main.tsp` is the source of truth for log events. Do not edit `backend/logging/events_gen.py` manually; update the TypeSpec schema and run `just gen-log-models` from the repository root.

## Tests

- Add focused unit tests alongside the existing `src/test/test_*.py` modules. Direct async function tests with `Mock(spec=AsyncSession)` and `AsyncMock` for awaited methods are an established pattern.
- Mark tests that need the running stack or real PostgreSQL with `pytest.mark.integration`. The integration suite expects the local backend to be reachable and uses Testcontainers for an isolated migrated database where appropriate.
- Keep seeded development and integration data deterministic by using the supplied seed and local random generator.
- Preserve or improve the configured branch-coverage threshold; do not exclude new application code merely to satisfy coverage.

## Verification

- Run `uv run poe check` for formatting, linting, and type checking.
- Run `uv run poe test` when the required local integration services are available.
