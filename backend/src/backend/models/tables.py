from enum import StrEnum
from enum import auto
from typing import Optional
from typing import final

from sqlmodel import Field
from sqlmodel import SQLModel


@final
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)


# WARNING: Changing the `GlobalKey` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class GlobalKey(StrEnum):
    FOOTER_TEXT = auto()


@final
class Global(SQLModel, table=True):
    __tablename__ = "globals"  # type: ignore[reportAssignmentType]

    key: GlobalKey = Field(primary_key=True)
    value: str


# WARNING: Changing the `StaticPageKind` enum requires also creating a database
#          migration to update the SQLAlchemy Enum type in the database.
@final
class StaticPageKind(StrEnum):
    IMPRINT = auto()


@final
class StaticPage(SQLModel, table=True):
    __tablename__ = "static_pages"  # type: ignore[reportAssignmentType]

    kind: StaticPageKind = Field(primary_key=True)
    content: str
