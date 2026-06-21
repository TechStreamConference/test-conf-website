import asyncio
import logging

_LOGGER = logging.getLogger(__name__)


async def main() -> None:
    _LOGGER.info("Hello, world!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)  # pragma: no cover
    asyncio.run(main())  # pragma: no cover
