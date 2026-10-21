from fastapi import APIRouter
from fastapi import status

import backend.routes.v1.auth
import backend.routes.v1.events
import backend.routes.v1.globals
import backend.routes.v1.imprint
import backend.routes.v1.users
from backend.models.responses import InternalServerErrorResponseV1

ROUTER = APIRouter(
    prefix="/v1",
    # Every endpoint can fail unexpectedly (e.g., because the database is unreachable).
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": InternalServerErrorResponseV1},
    },
)

ROUTER.include_router(backend.routes.v1.auth.ROUTER)
ROUTER.include_router(backend.routes.v1.events.ROUTER)
ROUTER.include_router(backend.routes.v1.globals.ROUTER)
ROUTER.include_router(backend.routes.v1.imprint.ROUTER)
ROUTER.include_router(backend.routes.v1.users.ROUTER)
