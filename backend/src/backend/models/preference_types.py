from typing import Annotated

from pydantic import AfterValidator

from backend.user_preferences import validate_locale

type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
