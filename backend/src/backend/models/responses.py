from typing import Literal
from typing import final

from pydantic import BaseModel

# class name should include the api version since the typescript generator uses the same name.
# This could lead to confusion within the frontend once a second api version gets introduced.


@final
class GlobalsResponseV1(BaseModel):
    footer_text: str


@final
class ImprintResponseV1(BaseModel):
    content: str


@final
class ImprintPageContentNotFoundResponseV1(BaseModel):
    detail: Literal["Imprint page not found in the database."] = "Imprint page not found in the database."
