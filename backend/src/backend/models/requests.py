from enum import StrEnum
from enum import auto
from typing import Optional
from typing import final

from pydantic import BaseModel
from pydantic import model_validator

from backend.models.preference_types import Bcp47Locale
from backend.models.preference_types import IanaTimezone


class RegionalSettingsDecision(StrEnum):
    ACCEPT = auto()
    KEEP = auto()


@final
class UserPreferencesInputV1(BaseModel):
    timezone: IanaTimezone
    locale: Bcp47Locale


@final
class ReportedRegionalSettingsInputV1(BaseModel):
    timezone: IanaTimezone
    locale: Bcp47Locale


@final
class RegionalSettingsDecisionInputV1(BaseModel):
    # Both are optional so they can be decided independently, but at least
    # one decision is required; explicit `null` is rejected by the type.
    timezone: Optional[RegionalSettingsDecision] = None
    locale: Optional[RegionalSettingsDecision] = None

    @model_validator(mode="after")
    def _require_at_least_one_decision(self) -> "RegionalSettingsDecisionInputV1":
        if self.timezone is None and self.locale is None:
            raise ValueError("At least one of `timezone` or `locale` must be decided.")
        return self
