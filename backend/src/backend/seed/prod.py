from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import GlobalKey
from backend.models.tables import GlobalTranslation
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind


async def seed_prod(session: AsyncSession) -> None:
    session.add(GlobalTranslation(key=GlobalKey.FOOTER_TEXT, language_tag="de", value="Fußzeile"))
    session.add(GlobalTranslation(key=GlobalKey.FOOTER_TEXT, language_tag="en", value="Footer"))
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language_tag="de", content="Impressum"))
    session.add(StaticPage(kind=StaticPageKind.IMPRINT, language_tag="en", content="Imprint"))

    await session.commit()
