from typing import Annotated

from pydantic import AfterValidator

from backend.user_preferences import validate_locale
from backend.user_preferences import validate_timezone

type IanaTimezone = Annotated[str, AfterValidator(validate_timezone)]
type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
