from typing import Annotated
from typing import Final
from typing import Optional

from fastapi import APIRouter
from fastapi import Depends
from fastapi import Query
from fastapi import status
from langcodes import Language

from backend.language_selection import LANGUAGE_SELECTION_DESCRIPTION
from backend.language_selection import LanguageRequest
from backend.language_selection import get_language_request
from backend.language_selection import select_language
from backend.language_tags import Bcp47LanguageTag
from backend.language_tags import parse_language
from backend.models.responses import DisplayLanguageResponseV1
from backend.models.responses import MissingSupportedLanguagesResponseV1
from backend.utils import create_http_exception

ROUTER = APIRouter()

# Frontends support a handful of languages. Every supported language is parsed and matched, so limiting them bounds the
# work a client can cause.
_MAX_SUPPORTED_LANGUAGES = 32


# TODO: Also respect the display language preference of logged-in users once it can be stored. Requires
#       `https://github.com/TechStreamConference/test-conf-website/issues/387` to be resolved first. Update
#       the description below accordingly.
@ROUTER.get(
    "/display-language",
    summary="Get language tag of the language in which the frontend should be displayed",
    description=(
        "The backend owns the algorithm that selects the language that should be displayed to the user. "
        + "Therefore, the frontend passes the languages it supports (`supported_language`, repeatable) and "
        + f"queries for the correct language tag (at most {_MAX_SUPPORTED_LANGUAGES} supported languages). "
        + "The returned tags are spelled exactly as passed in "
        + "`supported_language`; of several spellings of the same language, the first one is used. "
        + LANGUAGE_SELECTION_DESCRIPTION
    ),
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_400_BAD_REQUEST: {"model": MissingSupportedLanguagesResponseV1},
    },
    operation_id="get display language v1",
)
async def get_display_language(
    language_request: Annotated[LanguageRequest, Depends(get_language_request)],
    # Without `Query()`, FastAPI would expect a list parameter in the request body.
    supported_language: Annotated[
        Optional[list[Bcp47LanguageTag]],
        Query(max_length=_MAX_SUPPORTED_LANGUAGES),
    ] = None,
) -> DisplayLanguageResponseV1:
    if not supported_language:
        raise create_http_exception(
            status.HTTP_400_BAD_REQUEST,
            MissingSupportedLanguagesResponseV1(),
        )
    # Languages are selected by their normalized form, but returned in the client's spelling, so that the client
    # finds them in its own list.
    spelling_by_language: Final[dict[Language, str]] = {}
    for tag in supported_language:
        _ = spelling_by_language.setdefault(parse_language(tag), tag)
    language_details: Final = select_language(list(spelling_by_language), language_request)
    return DisplayLanguageResponseV1(
        available_languages=list(spelling_by_language.values()),
        language_tag=spelling_by_language[language_details.language_tag],
        is_language_fallback=language_details.is_language_fallback,
    )
