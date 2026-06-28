from typing import Optional
from typing import final

from sqlmodel import Field
from sqlmodel import SQLModel


@final
class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore[reportAssignmentType]

    id: Optional[int] = Field(default=None, primary_key=True)
