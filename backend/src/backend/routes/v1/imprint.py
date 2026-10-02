from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from langcodes import Language
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from backend.database import get_session
from backend.models.responses import ImprintPageContentNotFoundResponseV1
from backend.models.responses import ImprintResponseV1
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/{language_tag}/imprint",
    summary="Get the markdown contents of the imprint page",
    description="Retrieve the markdown contents of the imprint page stored in the database. "
    + "If the requested language is not available, English is returned instead, or, if that is "
    + "not available either, the first available language.",
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_404_NOT_FOUND: {"model": ImprintPageContentNotFoundResponseV1},
    },
    operation_id="get imprint v1",
)
async def get_imprint(language_tag: str, session: Annotated[AsyncSession, Depends(get_session)]) -> ImprintResponseV1:
    statement: Final = (
        select(StaticPage).where(col(StaticPage.kind) == StaticPageKind.IMPRINT).order_by(col(StaticPage.language_tag))
    )
    pages_by_language_tag: Final = {page.language_tag: page for page in (await session.execute(statement)).scalars()}
    if not pages_by_language_tag:
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            ImprintPageContentNotFoundResponseV1(),
        )

    imprint_page = pages_by_language_tag.get(language_tag)
    is_language_fallback: Final = imprint_page is None

    # If the requested language is missing, we first try to fall back to
    # English. Only if that is not available, we fall back to the first
    # available language.
    if imprint_page is None:
        imprint_page = pages_by_language_tag.get(str(Language.get("en")))
    if imprint_page is None:
        imprint_page = next(iter(pages_by_language_tag.values()))

    return ImprintResponseV1(
        content=imprint_page.content,
        available_languages=list(pages_by_language_tag),
        language_tag=imprint_page.language_tag,
        is_language_fallback=is_language_fallback,
    )
