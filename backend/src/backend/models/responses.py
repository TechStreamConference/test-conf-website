from typing import final

from pydantic import BaseModel
from pydantic import Field


@final
class GlobalsResponse(BaseModel):
    footer_text: str = Field(description="Text to be displayed in the footer of the website.")
    imprint_text: str = Field(
        description=(
            "Holds the text contents to be shown on the imprint page. "
            + "These contents are in Markdown format and have to be rendered accordingly by the frontend."
        )
    )
