import time
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


@app.exception_handler(Exception)
async def _handle_unexpected_exception(
    _request: Request,
    _exception: Exception,
) -> JSONResponse:
    # Starlette re-raises the exception after sending this response, so the traceback is still logged by the server.
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=InternalServerErrorResponseV1().model_dump(mode="json", by_alias=True),
    )


@app.middleware("http")
async def _log_requests(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    logging.info(HttpRequestReceived(method=request.method, path=request.url.path))
    start: Final = time.monotonic()
    response: Final = await call_next(request)
    logging.info(
        HttpRequestCompleted(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round((time.monotonic() - start) * 1000.0, 2),
        )
    )
    return response


@app.get(
    "/health/database",
    operation_id="backend health check",
)
async def database_health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, bool]:
    _ = await session.execute(text("select 1"))
    return {"ok": True}
