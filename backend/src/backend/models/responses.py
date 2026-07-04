from typing import final

from pydantic import BaseModel


@final
class GlobalsResponse(BaseModel):
    footer_text: str
