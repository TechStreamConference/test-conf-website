from typing import Annotated
from typing import Final

from fastapi import Depends
from fastapi import FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_session
from backend.routes import v1_api

app: Final = FastAPI()

app.include_router(v1_api.ROUTER)


@app.get(
    "/health/database",
    operation_id="backend health check",
)
async def database_health(session: Annotated[AsyncSession, Depends(get_session)]) -> dict[str, bool]:
    _ = await session.execute(text("select 1"))
    return {"ok": True}
