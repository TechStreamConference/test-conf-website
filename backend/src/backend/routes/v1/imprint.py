from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from backend.database import get_session
from backend.models.responses import ImprintPageContentNotFoundResponse
from backend.models.responses import ImprintResponse
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/imprint",
    summary="Get the markdown contents of the imprint page",
    description="Retrieve the markdown contents of the imprint page stored in the database.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ImprintPageContentNotFoundResponse},
    },
)
async def get_imprint(session: Annotated[AsyncSession, Depends(get_session)]) -> ImprintResponse:
    result: Final = await session.execute(select(StaticPage).where(StaticPage.kind == StaticPageKind.IMPRINT))
    imprint_page: Final = result.scalar_one_or_none()
    if imprint_page is None:
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            ImprintPageContentNotFoundResponse(),
        )
    return ImprintResponse(content=imprint_page.content)
