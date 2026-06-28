import asyncio
from enum import StrEnum
from enum import auto
from typing import Final
from typing import final

import typer

from backend.database import ASYNC_SESSION_FACTORY
from backend.seed.dev import seed_dev
from backend.seed.prod import seed_prod

app: Final = typer.Typer(no_args_is_help=True)


@final
class Environment(StrEnum):
    DEV = auto()
    PROD = auto()


@app.command()
def run(
    environment: Environment,
    num_users: int = 10,
    seed: int = 12345,
) -> None:
    asyncio.run(
        _run(
            environment=environment,
            num_users=num_users,
            seed=seed,
        )
    )


async def _run(
    *,
    environment: Environment,
    num_users: int,
    seed: int,
) -> None:
    async with ASYNC_SESSION_FACTORY() as session:
        match environment:
            case Environment.DEV:
                await seed_dev(session, num_users=num_users, seed=seed)
            case Environment.PROD:
                await seed_prod(session)


if __name__ == "__main__":
    app()
