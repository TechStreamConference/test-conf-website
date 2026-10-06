from typing import Annotated

from pydantic import AfterValidator

from backend.language_tags import validate_locale
from backend.timezones import validate_timezone

type IanaTimezone = Annotated[str, AfterValidator(validate_timezone)]
type Bcp47Locale = Annotated[str, AfterValidator(validate_locale)]
