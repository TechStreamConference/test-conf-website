import pytest

from backend.main import root


@pytest.mark.asyncio
async def test_root() -> None:
    response = await root()
    assert response == {"message": "Hello, world!"}
