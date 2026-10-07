import time
import traceback
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated
from typing import Final

from fastapi import Depends
from fastapi import FastAPI
from fastapi import Request
from fastapi import Response
from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.base import RequestResponseEndpoint

from backend import logging
from backend.config import SETTINGS
from backend.database import get_session
from backend.logging.events_gen import ApplicationStarted
from backend.logging.events_gen import ApplicationStopping
from backend.logging.events_gen import HttpRequestCompleted
from backend.logging.events_gen import HttpRequestFailed
from backend.logging.events_gen import HttpRequestReceived
from backend.models.responses import InternalServerErrorResponseV1
from backend.routes import v1_api


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None]:
    logging.info(ApplicationStarted(host=SETTINGS.server_host, port=SETTINGS.server_port))
    yield
    logging.info(ApplicationStopping())


app: Final = FastAPI(root_path=SETTINGS.backend_root_uri, lifespan=_lifespan)

app.include_router(v1_api.ROUTER)


@app.middleware("http")
async def _log_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    logging.info(HttpRequestReceived(method=request.method, path=request.url.path))
    start: Final = time.monotonic()
    try:
        response: Final = await call_next(request)
    except Exception as exception:
        # Unexpected exceptions are turned into the documented response here instead of being re-raised: Starlette
        # would pass them on to the server, which logs them as unstructured tracebacks including their message. The
        # message is never logged, since it may contain personal data (e.g. the values violating a constraint).
        exception_type: Final = type(exception)
        logging.error(
            HttpRequestFailed(
                method=request.method,
                path=request.url.path,
                exception_type=f"{exception_type.__module__}.{exception_type.__qualname__}",
                exception_stack=_code_locations(exception),
            )
        )
        _log_request_completed(request, status.HTTP_500_INTERNAL_SERVER_ERROR, start)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=InternalServerErrorResponseV1().model_dump(mode="json", by_alias=True),
        )
    _log_request_completed(request, response.status_code, start)
    return response


def _code_locations(exception: BaseException) -> str:
    """Describe where `exception` was raised by the code locations of its
    traceback, outermost first and one per line.

    Only module names, line numbers, and function names are included. Unlike
    file paths (e.g. of a home directory), they cannot contain personal data.
    """
    locations: Final[list[str]] = []
    for frame, line_number in traceback.walk_tb(exception.__traceback__):
        module: object = frame.f_globals.get("__name__")
        locations.append(f"{module if isinstance(module, str) else '?'}:{line_number} in {frame.f_code.co_qualname}")
    return "\n".join(locations)


def _log_request_completed(request: Request, status_code: int, start: float) -> None:
    logging.info(
        HttpRequestCompleted(
            method=request.method,
            path=request.url.path,
            status_code=status_code,
            duration_ms=round((time.monotonic() - start) * 1000.0, 2),
        )
    )


@app.get(
    "/health/database",
    operation_id="backend health check",
)
async def database_health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, bool]:
    _ = await session.execute(text("select 1"))
    return {"ok": True}
