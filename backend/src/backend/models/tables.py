from datetime import UTC
from datetime import datetime
from enum import StrEnum
from enum import auto
from typing import Optional
from typing import final

from sqlmodel import Field
from sqlmodel import SQLModel


def _utc_now() -> datetime:
    return datetime.now(UTC)



@final
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utc_now, nullable=False)


# WARNING: Changing the `GlobalKey` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class GlobalKey(StrEnum):
    FOOTER_TEXT = auto()
    IMPRINT_TEXT = auto()


@final
class Global(SQLModel, table=True):
    __tablename__ = "globals"  # type: ignore[reportAssignmentType]

    key: GlobalKey = Field(primary_key=True)
    value: str
