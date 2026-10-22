from typing import Annotated
from typing import Final

from pydantic import StringConstraints

# The syntax of a content language: a lowercase primary language subtag.
CONTENT_LANGUAGE_TAG_PATTERN: Final = r"^[a-z]{2,3}$"

# A language that translated content is stored in.
type ContentLanguageTag = Annotated[str, StringConstraints(pattern=CONTENT_LANGUAGE_TAG_PATTERN)]
