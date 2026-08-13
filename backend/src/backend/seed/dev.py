# ruff: noqa: S311  # `random` is used for reproducible fake data, not cryptography.
import random
from datetime import date
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Final
from typing import NamedTuple
from typing import final

from faker import Faker
from langcodes import Language
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.tables import Event
from backend.models.tables import EventTranslation
from backend.models.tables import Global
from backend.models.tables import GlobalKey
from backend.models.tables import StaticPage
from backend.models.tables import StaticPageKind
from backend.models.tables import User

# To avoid putting large bodies of text into the code, we store them in
# separate files. These live under the `./data` directory.
_DATA_PATH = Path(__file__).parent / "data"

_CONFERENCE_NAME = "Tech Stream Conference"

_FAKER_LOCALES_BY_BCP_47_LANGUAGE_TAG = {
    Language.get("de"): "de_DE",
    Language.get("en"): "en_US",
    Language.get("es"): "es_ES",
}


@final
class EventSpec(NamedTuple):
    year: int
    languages: list[Language]


# Most years have one entry (the default), but a year may appear multiple times
# (multiple events) or not at all (no event that year).
_EVENTS: list[EventSpec] = [
    EventSpec(2022, [Language.get("de")]),
    EventSpec(2023, [Language.get("de"), Language.get("en")]),
    EventSpec(2024, [Language.get("de")]),  # Two events in 2024.
    EventSpec(2024, [Language.get("de"), Language.get("en"), Language.get("es")]),
    # 2025: no event
    EventSpec(2026, [Language.get("de"), Language.get("en")]),
    EventSpec(2027, [Language.get("de"), Language.get("en"), Language.get("es")]),
    EventSpec(2028, [Language.get("de"), Language.get("en")]),  # Two events in 2028.
    EventSpec(2028, [Language.get("de")]),
    EventSpec(2029, [Language.get("de"), Language.get("en")]),
]


async def seed_dev(session: AsyncSession, *, num_users: int, seed: int) -> None:
    rng: Final = random.Random(seed)
    Faker.seed(seed)
    fakers_by_language: Final = {
        language: Faker(locale) for language, locale in _FAKER_LOCALES_BY_BCP_47_LANGUAGE_TAG.items()
    }

    _seed_users_table(session, num_users)
    _seed_globals_table(session)
    _seed_static_pages_table(session)
    await _seed_events_data(
        session,
        rng=rng,
        fakers_by_language=fakers_by_language,
    )

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
    }.items():
        session.add(Global(key=key, value=value))


def _seed_static_pages_table(session: AsyncSession) -> None:
    for kind, content_file in {
        StaticPageKind.IMPRINT: _DATA_PATH / "imprint.md",
    }.items():
        session.add(
            StaticPage(
                kind=kind,
                content=content_file.read_text(
                    encoding="utf-8",
                ),
            )
        )


def _date_to_datetime(date: date) -> datetime:
    return datetime(
        date.year,
        date.month,
        date.day,
    )


def _random_date_before(
    rng: random.Random,
    before: date,
    *,
    window_start: date,
    prefer_min_days: int,
    prefer_max_days: int,
) -> date | None:
    """Return a random date in [window_start, before - 1].

    Prefers the sub-window [before - prefer_max_days, before - prefer_min_days];
    falls back to the full [window_start, before - 1] if the preferred window
    does not fit. Returns None only when window_start >= before.
    """
    hard_latest = before - timedelta(days=1)
    if window_start > hard_latest:
        return None
    soft_earliest = max(window_start, before - timedelta(days=prefer_max_days))
    soft_latest = min(hard_latest, before - timedelta(days=prefer_min_days))
    if soft_earliest <= soft_latest:
        return soft_earliest + timedelta(days=rng.randint(0, (soft_latest - soft_earliest).days))
    # Preferred window too tight; use the full available window.
    return window_start + timedelta(days=rng.randint(0, (hard_latest - window_start).days))


def _optional_datetime_before(
    rng: random.Random,
    before: date,
    window_start: date,
    condition: bool,
    prefer_min_days: int,
    prefer_max_days: int,
) -> datetime | None:
    if not condition:
        return None
    d = _random_date_before(
        rng, before, window_start=window_start, prefer_min_days=prefer_min_days, prefer_max_days=prefer_max_days
    )
    return _date_to_datetime(d) if d else None


async def _seed_events_data(
    session: AsyncSession,
    *,
    rng: random.Random,
    fakers_by_language: dict[Language, Faker],
) -> None:
    # All milestone dates for event N must not precede the end of event N-1.
    # Initialize to a sentinel that imposes no constraint on the first event.
    prev_end_date = date(_EVENTS[0].year - 1, 12, 31)

    for event_spec in _EVENTS:
        year = event_spec.year

        # Start date: pick a spring/summer/autumn date after the previous event ended.
        earliest_start = max(date(year, 3, 1), prev_end_date + timedelta(days=1))
        latest_start = date(year, 10, 25)
        if earliest_start > latest_start:
            latest_start = earliest_start
        start_date = earliest_start + timedelta(days=rng.randint(0, (latest_start - earliest_start).days))
        end_date = start_date + timedelta(days=rng.randint(1, 2))

        # All milestone dates must fall in [`prev_end_date`, `start_date`).
        publish_date = _random_date_before(
            rng,
            start_date,
            window_start=prev_end_date,
            prefer_min_days=90,
            prefer_max_days=150,
        )
        publish_datetime = _date_to_datetime(publish_date) if publish_date else None

        has_call_for_papers = rng.random() > 0.2
        call_for_papers_start_date = (
            _random_date_before(
                rng,
                start_date,
                window_start=prev_end_date,
                prefer_min_days=150,
                prefer_max_days=180,
            )
            if has_call_for_papers
            else None
        )
        # `call_for_papers_end` must come after `call_for_papers_start`, so use it as the `window_start`.
        call_for_papers_end_date = (
            _random_date_before(
                rng,
                start_date,
                window_start=call_for_papers_start_date + timedelta(days=1),
                prefer_min_days=30,
                prefer_max_days=60,
            )
            if call_for_papers_start_date is not None
            else None
        )
        call_for_papers_start_datetime = (
            _date_to_datetime(call_for_papers_start_date) if call_for_papers_start_date else None
        )
        call_for_papers_end_datetime = _date_to_datetime(call_for_papers_end_date) if call_for_papers_end_date else None

        spotlight = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.4, 14, 30)
        speakers_visible = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.3, 30, 60)
        sponsors_visible = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.3, 60, 90)
        media_partners_visible = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.5, 60, 90)
        team_members_visible = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.5, 30, 60)
        schedule_visible = _optional_datetime_before(rng, start_date, prev_end_date, rng.random() > 0.3, 7, 21)

        event = Event(
            start_date=start_date,
            end_date=end_date,
            discord_url="https://discord.gg/techstream" if rng.random() > 0.3 else None,
            twitch_url="https://twitch.tv/techstream" if rng.random() > 0.4 else None,
            youtube_channel_url="https://youtube.com/@techstreamconference" if rng.random() > 0.3 else None,
            publish_date=publish_datetime,
            call_for_papers_start=call_for_papers_start_datetime,
            call_for_papers_end=call_for_papers_end_datetime,
            frontpage_spotlight_date=spotlight,
            speakers_visible_from=speakers_visible,
            sponsors_visible_from=sponsors_visible,
            media_partners_visible_from=media_partners_visible,
            team_members_visible_from=team_members_visible,
            schedule_visible_from=schedule_visible,
        )
        session.add(event)
        await session.flush()  # Populate `event.id` before creating translations.
        if event.id is None:
            raise RuntimeError("event.id was not populated after flush")

        for language in event_spec.languages:
            faker = fakers_by_language[language]

            has_trailer = rng.random() > 0.5
            has_subtitles = has_trailer and rng.random() > 0.5
            session.add(
                EventTranslation(
                    event_id=event.id,
                    language_tag=str(language),
                    title=f"{_CONFERENCE_NAME} {year}",
                    subtitle=faker.sentence(nb_words=6).rstrip("."),
                    description_headline=faker.sentence(nb_words=4).rstrip("."),
                    description=faker.paragraph(nb_sentences=5),
                    presskit_url=f"https://example.com/presskit/{year}/{language}" if rng.random() > 0.5 else None,
                    trailer_url=f"https://youtube.com/watch?v=techstream{year}{language}" if has_trailer else None,
                    trailer_poster_url=(
                        f"https://example.com/trailer/{year}/{language}/poster.jpg" if has_trailer else None
                    ),
                    trailer_subtitles_url=(
                        f"https://example.com/trailer/{year}/{language}/subtitles.vtt" if has_subtitles else None
                    ),
                )
            )

        prev_end_date = end_date
