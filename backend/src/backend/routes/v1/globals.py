from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.database import get_session
from backend.models.responses import GlobalsResponseV1
from backend.models.tables import Global
from backend.models.tables import GlobalKey

ROUTER = APIRouter()


@ROUTER.get(
    "/globals",
    summary="Get global configuration values",
    description="Retrieve all global key-value configuration pairs stored in the database.",
    status_code=status.HTTP_200_OK,
    operation_id="get globals v1",
)
async def get_globals(session: Annotated[AsyncSession, Depends(get_session)]) -> GlobalsResponseV1:
    result: Final = await session.execute(select(Global))
    globals_map: Final = {row.key: row.value for row in result.scalars().all()}
    return GlobalsResponseV1(
        footer_text=globals_map[GlobalKey.FOOTER_TEXT],
    )
