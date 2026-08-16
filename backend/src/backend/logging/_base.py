"""Base class for all typed log event models."""

from typing import ClassVar

from pydantic import BaseModel
from pydantic import ConfigDict


class LogEventBase(BaseModel):
    """Base class for all typed log event models.

    Generated subclasses set ``LOG_EVENT_NAME`` and ``LOG_BODY`` as class-level
    constants.  The logging facade reads them without requiring callers to pass
    that information manually.
    """

    model_config = ConfigDict(frozen=True)

    LOG_EVENT_NAME: ClassVar[str]
    LOG_BODY: ClassVar[str]
