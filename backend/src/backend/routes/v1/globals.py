from fastapi import APIRouter

ROUTER = APIRouter()


@ROUTER.get("/globals")
async def get_globals() -> str:
    return "This is the globals endpoint"
