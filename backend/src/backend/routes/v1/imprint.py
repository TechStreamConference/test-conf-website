from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from backend.database import get_session
from backend.language_selection import LANGUAGE_SELECTION_DESCRIPTION
from backend.language_selection import LanguageRequest
from backend.language_selection import get_language_request
from backend.language_selection import select_translation
from backend.models.responses import ImprintPageContentNotFoundResponseV1
from backend.models.responses import ImprintResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/imprint",
    summary="Get the markdown contents of the imprint page",
    description=(
        f"Retrieve the markdown contents of the imprint page stored in the database. {LANGUAGE_SELECTION_DESCRIPTION}"
    ),
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ImprintPageContentNotFoundResponseV1},
    },
    operation_id="get imprint v1",
)
async def get_imprint(
    session: Annotated[AsyncSession, Depends(get_session)],
    language_request: Annotated[LanguageRequest, Depends(get_language_request)],
) -> ImprintResponseV1:
    pages_by_language: Final = {
        page.language: page
        for page in (
            await session.execute(
                select(StaticPage)
                .where(col(StaticPage.kind) == StaticPageKind.IMPRINT)
                .order_by(col(StaticPage.language))
            )
        ).scalars()
    }
    if not pages_by_language:
        # This page does not exist in the database.
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            ImprintPageContentNotFoundResponseV1(),
        )

    selected: Final = select_translation(pages_by_language, language_request)

    return ImprintResponseV1(
        content=selected.translation.content,
        language_details=selected.language_details,
    )
