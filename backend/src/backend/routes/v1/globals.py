from collections import defaultdict
from typing import Annotated
from typing import Final

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Response
from fastapi import status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from backend.content_language_selection import CONTENT_LANGUAGE_RESPONSE_HEADERS
from backend.content_language_selection import get_requested_language_ranges
from backend.content_language_selection import language_details_v1_from_selection
from backend.content_language_selection import select_content_language
from backend.database import get_session
from backend.models.responses import GlobalsNotFoundResponseV1
from backend.models.responses import GlobalsResponseV1
from backend.models.responses import UnsupportedLanguageTagResponseV1
from backend.models.tables import ContentLanguage
from backend.models.tables import GlobalKey
from backend.models.tables import GlobalTranslation
from backend.utils import create_http_exception

ROUTER = APIRouter()


@ROUTER.get(
    "/globals",
    summary="Get global configuration values",
    description=(
        "Retrieve the global configuration values stored in the database in one language. "
        + "The requested `language` is matched by its primary language subtag (`de-AT` delivers `de`). "
        + "If it is not available, English is returned instead, or, if that is not available either, "
        + "the lexicographically first available language."
    ),
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_200_OK: {"model": GlobalsResponseV1, "headers": CONTENT_LANGUAGE_RESPONSE_HEADERS},
        status.HTTP_404_NOT_FOUND: {"model": GlobalsNotFoundResponseV1},
        status.HTTP_422_UNPROCESSABLE_CONTENT: {"model": UnsupportedLanguageTagResponseV1},
    },
    operation_id="get globals v1",
)
async def get_globals(
    language_ranges: Annotated[list[str], Depends(get_requested_language_ranges)],
    response: Response,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> GlobalsResponseV1:
    statement: Final = (
        select(GlobalTranslation, col(ContentLanguage.name))
        .join(
            ContentLanguage,
            col(ContentLanguage.tag) == col(GlobalTranslation.language_tag),
        )
        .order_by(col(GlobalTranslation.language_tag))
    )
    values_by_language_tag: Final[defaultdict[str, dict[GlobalKey, str]]] = defaultdict(dict)
    language_names: Final[dict[str, str]] = {}
    for translation, language_name in (await session.execute(statement)).all():
        values_by_language_tag[translation.language_tag][translation.key] = translation.value
        language_names[translation.language_tag] = language_name
    # A language counts as available only if it has a value for every key.
    complete_values_by_language_tag: Final = {
        language_tag: values for language_tag, values in values_by_language_tag.items() if len(values) == len(GlobalKey)
    }

    if not complete_values_by_language_tag:
        raise create_http_exception(
            status.HTTP_404_NOT_FOUND,
            GlobalsNotFoundResponseV1(),
        )

    selection: Final = select_content_language(language_ranges, complete_values_by_language_tag)
    response.headers["Content-Language"] = selection.language_tag
    values: Final = complete_values_by_language_tag[selection.language_tag]

    return GlobalsResponseV1(
        footer_text=values[GlobalKey.FOOTER_TEXT],
        language_details=language_details_v1_from_selection(selection, language_names),
    )
