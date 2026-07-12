from typing import Literal
from typing import final

from pydantic import BaseModel


@final
class GlobalsResponse(BaseModel):
    footer_text: str


@final
class ImprintResponse(BaseModel):
    content: str


@final
class ImprintPageContentNotFoundResponse(BaseModel):
    detail: Literal["Imprint page not found in the database."] = "Imprint page not found in the database."
