from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import User


async def seed_dev(session: AsyncSession, *, num_users: int, seed: int) -> None:
    # We don’t have random data yet, but we will in the future,
    # so we’ll keep the `seed` parameter for now.
    _ = seed

    for _ in range(num_users):
        session.add(User())

    await session.commit()
