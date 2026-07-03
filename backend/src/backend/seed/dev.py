from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Global
from backend.models.tables import GlobalKey
from backend.models.tables import User


async def seed_dev(session: AsyncSession, *, num_users: int, seed: int) -> None:
    # We don’t have random data yet, but we will in the future,
    # so we’ll keep the `seed` parameter for now.
    _ = seed

    for _ in range(num_users):
        session.add(User())

    session.add(
        Global(
            key=GlobalKey.FOOTER_TEXT,
            value=(
                "TECH STREAM CONFERENCE – Online-Konferenz mit Vorträgen aus den "
                + "Bereichen Programmierung, Maker-Szene und Spieleentwicklung"
            ),
        )
    )

    await session.commit()
