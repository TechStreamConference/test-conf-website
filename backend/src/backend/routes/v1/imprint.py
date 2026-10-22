from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from backend.content_language_selection import get_requested_language_ranges
from backend.content_language_selection import select_content_language
from backend.database import get_session
from backend.models.responses import ImprintPageContentNotFoundResponseV1
from backend.models.responses import ImprintResponseV1
from backend.models.responses import LanguageDetailsV1
from backend.models.responses import UnsupportedLanguageTagResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/imprint",
    summary="Get the markdown contents of the imprint page",
    description="Retrieve the markdown contents of the imprint page stored in the database. "
    + "The requested `language` is matched by its primary language subtag (`de-AT` delivers `de`). "
    + "If it is not available, English is returned instead, or, if that is not available either, "
    + "the lexicographically first available language.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ImprintPageContentNotFoundResponseV1},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": UnsupportedLanguageTagResponseV1},
    },
    operation_id="get imprint v1",
)
async def get_imprint(
    language_ranges: Annotated[list[str], Depends(get_requested_language_ranges)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ImprintResponseV1:
    statement: Final = (
        select(StaticPage).where(col(StaticPage.kind) == StaticPageKind.IMPRINT).order_by(col(StaticPage.language_tag))
    )
    pages_by_language_tag: Final = {page.language_tag: page for page in (await session.execute(statement)).scalars()}
    if not pages_by_language_tag:
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            ImprintPageContentNotFoundResponseV1(),
        )

    selection: Final = select_content_language(language_ranges, pages_by_language_tag)
    response.headers["Content-Language"] = selection.language_tag

    return ImprintResponseV1(
        content=pages_by_language_tag[selection.language_tag].content,
        language_details=LanguageDetailsV1(
            available_languages=selection.available_languages,
            language_tag=selection.language_tag,
            is_language_fallback=selection.is_language_fallback,
        ),
    )
