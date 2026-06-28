from sqlalchemy.ext.asyncio import AsyncSession


async def seed_prod(session: AsyncSession) -> None:
    # Intentionally empty for now.
    await session.commit()
