"""Every seeder has to provide the static content in all supported display languages."""

from collections import defaultdict
from collections.abc import Awaitable
from collections.abc import Callable
from typing import Final
from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from backend.content_languages import SUPPORTED_DISPLAY_LANGUAGES
from backend.models.tables import Event
from backend.models.tables import GlobalKey
from backend.models.tables import GlobalTranslation
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.seed.dev import seed_dev
from backend.seed.prod import seed_prod

type _Seeder = Callable[[AsyncSession], Awaitable[None]]

_SEEDERS: dict[str, _Seeder] = {
    "dev": lambda session: seed_dev(session, num_users=1, seed=1),
    "prod": seed_prod,
}


async def _seed(seeder: _Seeder) -> list[object]:
    """Runs the seeder against a session that records what is added to it."""
    added: Final[list[object]] = []
    session: Final = Mock(spec=AsyncSession)
    session.add = Mock(side_effect=added.append)
    session.commit = AsyncMock()

    async def assign_event_ids() -> None:
        for index, row in enumerate(added, start=1):
            if isinstance(row, Event) and row.id is None:
                row.id = index

    session.flush = AsyncMock(side_effect=assign_event_ids)
    await seeder(session)
    return added


@pytest.mark.asyncio
@pytest.mark.parametrize("seeder", _SEEDERS.values(), ids=_SEEDERS.keys())
async def test_seeders_provide_every_static_page_in_all_supported_languages(seeder: _Seeder) -> None:
    added: Final = await _seed(seeder)
    languages_by_kind: Final[defaultdict[StaticPageKind, set[str]]] = defaultdict(set)
    for row in added:
        if isinstance(row, StaticPage):
            languages_by_kind[row.kind].add(row.language_tag)

    for kind in StaticPageKind:
        missing = SUPPORTED_DISPLAY_LANGUAGES - languages_by_kind[kind]
        assert not missing, f"The static page {kind} is not seeded in the supported languages {sorted(missing)}."


@pytest.mark.asyncio
@pytest.mark.parametrize("seeder", _SEEDERS.values(), ids=_SEEDERS.keys())
async def test_seeders_provide_every_global_value_in_all_supported_languages(seeder: _Seeder) -> None:
    added: Final = await _seed(seeder)
    languages_by_key: Final[defaultdict[GlobalKey, set[str]]] = defaultdict(set)
    for row in added:
        if isinstance(row, GlobalTranslation):
            languages_by_key[row.key].add(row.language_tag)

    for key in GlobalKey:
        missing = SUPPORTED_DISPLAY_LANGUAGES - languages_by_key[key]
        assert not missing, f"The global value {key} is not seeded in the supported languages {sorted(missing)}."
