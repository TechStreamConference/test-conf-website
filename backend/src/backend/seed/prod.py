from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Global
from backend.models.tables import GlobalKey


async def seed_prod(session: AsyncSession) -> None:
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
