from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Global
from backend.models.tables import GlobalKey


async def seed_prod(session: AsyncSession) -> None:
    session.add(Global(key=GlobalKey.FOOTER_TEXT, value="Footer"))
    session.add(Global(key=GlobalKey.IMPRINT_TEXT, value="Imprint"))

    await session.commit()
