from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Global
from backend.models.tables import GlobalKey
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind


async def seed_prod(session: AsyncSession) -> None:
    session.add(Global(key=GlobalKey.FOOTER_TEXT, value="Footer"))
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, content="Imprint"))

    await session.commit()
