import asyncio
from collections.abc import Awaitable
from collections.abc import Callable
from datetime import timedelta
from typing import Final

import httpx2
from sqlalchemy import text

from backend import logging
from backend.config import SETTINGS
from backend.database import ASYNC_SESSION_FACTORY
from backend.logging.events_gen import DependencyCheckFailed
from backend.models.dependency_status import DependencyStatus
from backend.models.responses import DependencyStatusesV1
from backend.utils import qualified_type_name

# Upper bound for a single dependency check, so that an unresponsive dependency
# is reported as down instead of stalling the health check.
_CHECK_TIMEOUT = timedelta(seconds=3)

_OIDC_DISCOVERY_URL = f"{SETTINGS.zitadel_issuer.rstrip('/')}/.well-known/openid-configuration"


async def _check_database() -> None:
    async with ASYNC_SESSION_FACTORY() as session:
        _ = await session.execute(text("select 1"))


async def _check_identity_provider() -> None:
    # OIDC discovery is the first request each login makes to the identity provider.
    async with httpx2.AsyncClient() as client:
        response: Final = await client.get(_OIDC_DISCOVERY_URL)
        _ = response.raise_for_status()


async def _status_of(dependency: str, check: Callable[[], Awaitable[None]]) -> DependencyStatus:
    try:
        async with asyncio.timeout(_CHECK_TIMEOUT.total_seconds()):
            await check()
    # Any failure, whatever its type, means that the dependency is down.
    except Exception as exception:
        logging.warning(
            DependencyCheckFailed(
                dependency=dependency,
                exception_type=qualified_type_name(exception),
            ),
        )
        return DependencyStatus.DOWN
    return DependencyStatus.UP


async def check_dependencies() -> DependencyStatusesV1:
    """Check all dependencies of the backend concurrently."""
    database, identity_provider = await asyncio.gather(
        _status_of("database", _check_database),
        _status_of("identity_provider", _check_identity_provider),
    )
    return DependencyStatusesV1(database=database, identity_provider=identity_provider)
