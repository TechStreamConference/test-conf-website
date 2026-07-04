from fastapi import APIRouter

import backend.routes.v1.globals

ROUTER = APIRouter(
    prefix="/v1",
)

ROUTER.include_router(backend.routes.v1.globals.ROUTER)
