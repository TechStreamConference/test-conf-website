from typing import Final

from fastapi import HTTPException
from pydantic import BaseModel


def create_http_exception(status_code: int, body: BaseModel) -> HTTPException:
    """
    Create an `HTTPException` with a detail payload derived from a Pydantic model.
    Note: FastAPI wraps `exc.detail` into a top-level `{"detail": exc.detail}`. If the
    provided model only contains a `detail` field, we unwrap it to avoid returning
    `{"detail": {"detail": "..."}}`.
    """
    dumped: Final = body.model_dump()
    detail: Final = dumped["detail"] if set(dumped.keys()) == {"detail"} else dumped
    return HTTPException(
        status_code=status_code,
        detail=detail,
    )
