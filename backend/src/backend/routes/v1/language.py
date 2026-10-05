from typing import Annotated
from typing import Final
from typing import Optional

from fastapi import APIRouter
from fastapi import Header
from fastapi import Query
from fastapi import Response
from fastapi import status

from backend.language_selection import LANGUAGE_SELECTION_DESCRIPTION
from backend.language_selection import select_translation
from backend.language_tags import Bcp47Language
from backend.models.responses import LanguageDetailsV1
from backend.models.responses import MissingSupportedLanguagesResponseV1
from backend.utils import create_http_exception

ROUTER = APIRouter()


# TODO: Also respect the display language preference of logged-in users once it can be stored. Requires
#       `https://github.com/TechStreamConference/test-conf-website/issues/387` to be resolved first. Update
#       the description below accordingly.
@ROUTER.get(
    "/display-language",
    summary="Get language tag of the language in which the frontend should be displayed",
    description=(
        "The backend owns the algorithm that selects the language that should be displayed to the user. "
        + "Therefore, the frontend passes the languages it supports (`supported_language`, repeatable) and "
        + "queries for the correct language tag. "
        + LANGUAGE_SELECTION_DESCRIPTION
    ),
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": MissingSupportedLanguagesResponseV1},
    },
    operation_id="get display language v1",
)
async def get_display_language(
    response: Response,
    language: Optional[Bcp47Language] = None,
    # Without `Query()`, FastAPI would expect a list parameter in the request body.
    supported_language: Annotated[Optional[list[Bcp47Language]], Query()] = None,
    accept_language: Annotated[Optional[str], Header()] = None,
) -> LanguageDetailsV1:
    if not supported_language:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            MissingSupportedLanguagesResponseV1(),
        )
    supported_languages_by_language: Final = {supported: supported for supported in supported_language}
    selected: Final = select_translation(
        supported_languages_by_language,
        language=language,
        accept_language=accept_language,
        response=response,
    )
    return selected.language_details
