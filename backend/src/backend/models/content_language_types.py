from typing import Annotated

from pydantic import StringConstraints

# A language that translated content is stored in: a lowercase primary language
# subtag, matching the check constraint of the `content_languages` table.
type ContentLanguageTag = Annotated[str, StringConstraints(pattern=r"^[a-z]{2,3}$")]
