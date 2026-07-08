from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Global
from backend.models.tables import GlobalKey
from backend.models.tables import User

# To avoid putting large bodies of text into the code, we store them in
# separate files. These live under the `./data` directory.
_DATA_PATH = Path(__file__).parent / "data"


async def seed_dev(session: AsyncSession, *, num_users: int, seed: int) -> None:
    # We don’t have random data yet, but we will in the future,
    # so we’ll keep the `seed` parameter for now.
    _ = seed

    _seed_users_table(session, num_users)
    _seed_globals_table(session)

    await session.commit()


def _seed_users_table(session: AsyncSession, num_users: int) -> None:
    for _ in range(num_users):
        session.add(User())


def _seed_globals_table(session: AsyncSession) -> None:
    for key, value in {
        GlobalKey.FOOTER_TEXT: (
            "TECH STREAM CONFERENCE – Online-Konferenz mit Vorträgen aus den "
            + "Bereichen Programmierung, Maker-Szene und Spieleentwicklung"
        ),
        GlobalKey.IMPRINT_TEXT: (_DATA_PATH / "imprint.md").read_text(encoding="utf-8"),
    }.items():
        session.add(Global(key=key, value=value))
