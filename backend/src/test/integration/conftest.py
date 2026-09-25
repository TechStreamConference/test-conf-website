import time
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Final

import httpx
import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from testcontainers.community.postgres import PostgresContainer

from alembic import command
from backend.config import SETTINGS
from backend.seed.cli import Environment
from backend.seed.cli import _run  # type: ignore[reportPrivateUsage]

_POSTGRES = PostgresContainer("postgres:16-alpine")
_MIGRATIONS_PATH = Path(__file__).resolve().parents[3] / "alembic"
_MAX_BACKEND_REACHABILITY_ATTEMPTS = 5
_BACKEND_REACHABILITY_RETRY_DELAY_SECONDS = 1.0


@pytest.fixture(scope="package")
def backend_is_reachable() -> bool:
    # Share one reachability check between the explicit backend test and the
    # integration setup, which skips the remaining integration tests when the
    # backend is unavailable.
    # CI starts the backend in a separate process, so tolerate brief transient
    # failures after its initial readiness probe.
    for attempt in range(_MAX_BACKEND_REACHABILITY_ATTEMPTS):
        try:
            response = httpx.get(
                f"{SETTINGS.backend_root_uri}/openapi.json",
                timeout=2.0,
            )
        except httpx.RequestError:
            pass
        else:
            if response.is_success:
                return True

        if attempt + 1 < _MAX_BACKEND_REACHABILITY_ATTEMPTS:
            time.sleep(_BACKEND_REACHABILITY_RETRY_DELAY_SECONDS)

    return False


@pytest_asyncio.fixture(scope="package")
async def migrate_and_seed_database(backend_is_reachable: bool) -> AsyncGenerator[str]:
    if not backend_is_reachable:
        pytest.skip("The remaining integration tests require a reachable backend.")

    _ = _POSTGRES.start()
    try:
        alembic_config: Final = Config()
        alembic_config.set_main_option("script_location", str(_MIGRATIONS_PATH))
        alembic_config.set_main_option("sqlalchemy.url", _POSTGRES.get_connection_url())
        command.upgrade(alembic_config, "head")

        engine: Final = create_async_engine(
            _POSTGRES.get_connection_url(driver="asyncpg"),
            echo=True,
            pool_pre_ping=True,
        )
        factory: Final = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        await _run(
            environment=Environment.DEV,
            num_users=10,
            seed=12345,
            session_factory_override=factory,
        )

        await engine.dispose()
        yield _POSTGRES.get_connection_url(driver="asyncpg")
    finally:
        _POSTGRES.stop()
