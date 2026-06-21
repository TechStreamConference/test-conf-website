import logging

import pytest

from backend.main import main


@pytest.mark.asyncio
async def test_main(caplog: pytest.LogCaptureFixture) -> None:
    caplog.set_level(logging.INFO)
    await main()
    assert "Hello, world!" in caplog.text
