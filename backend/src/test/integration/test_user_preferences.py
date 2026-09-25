import asyncio
from datetime import timedelta
from typing import Final
from typing import Optional

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine
from sqlmodel import select

from backend.models.requests import RegionalSettingsDecision
from backend.models.requests import RegionalSettingsDecisionInputV1
from backend.models.requests import ReportedRegionalSettingsInputV1
from backend.models.tables import Account
from backend.models.tables import RegionalSettingsSuggestion
from backend.models.tables import ReportedRegionalSettings
from backend.models.tables import User
from backend.models.tables import UserPreferences
from backend.models.tables import UserSession
from backend.routes.v1.users import decide_regional_settings_change
from backend.routes.v1.users import report_regional_settings
from backend.session import AuthenticatedSession
from backend.utils import utc_now

pytestmark: Final = pytest.mark.integration


async def _create_user_with_session(session_factory: async_sessionmaker[AsyncSession], *, token: str) -> UserSession:
    async with session_factory() as setup_session:
        user: Final = User()
        setup_session.add(user)
        await setup_session.commit()
        assert user.id is not None

        now: Final = utc_now()
        user_session: Final = UserSession(
            user_id=user.id,
            token_hash=token,
            expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=30),
        )
        setup_session.add(user_session)
        await setup_session.commit()
        assert user_session.id is not None
        return user_session


@pytest.mark.asyncio
async def test_concurrent_reports_for_the_same_session_serialize_via_the_row_lock(
    migrate_and_seed_database: str,
) -> None:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="concurrency-report-token")
        account: Final = Account(
            user_id=user_session.user_id,
            zitadel_user_id="concurrency-test",
            email="user@example.com",
            username="test-user",
        )

        async def report(timezone: str, locale: str) -> None:
            async with session_factory() as session:
                loaded_session: Final = await session.get(UserSession, user_session.id)
                assert loaded_session is not None
                authenticated: Final = AuthenticatedSession(account=account, session=loaded_session)
                await report_regional_settings(
                    ReportedRegionalSettingsInputV1(timezone=timezone, locale=locale),
                    authenticated,
                    session,
                )

        _ = await asyncio.gather(
            report("Europe/Berlin", "de-DE"),
            report("America/New_York", "en-US"),
        )

        async with session_factory() as verification_session:
            stored_preferences: Final = await verification_session.get(UserPreferences, user_session.user_id)
            stored_report: Final = await verification_session.get(ReportedRegionalSettings, user_session.id)
            assert stored_preferences is not None
            assert stored_report is not None
            # The row lock serializes the two reports: the preference is
            # whichever committed first, and the reported values are
            # whichever committed last (the session’s own latest state).
            assert (stored_preferences.timezone, stored_preferences.locale) in {
                ("Europe/Berlin", "de-DE"),
                ("America/New_York", "en-US"),
            }
            assert (stored_report.timezone, stored_report.locale) in {
                ("Europe/Berlin", "de-DE"),
                ("America/New_York", "en-US"),
            }
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_report_then_decision_flow_against_postgres(migrate_and_seed_database: str) -> None:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="decision-flow-token")
        account: Final = Account(
            user_id=user_session.user_id,
            zitadel_user_id="decision-flow-test",
            email="user@example.com",
            username="test-user",
        )

        async def authenticated(session: AsyncSession) -> AuthenticatedSession:
            loaded_session: Final = await session.get(UserSession, user_session.id)
            assert loaded_session is not None
            return AuthenticatedSession(account=account, session=loaded_session)

        # First report initializes both preferences; no suggestion is created.
        async with session_factory() as session:
            await report_regional_settings(
                ReportedRegionalSettingsInputV1(timezone="Europe/Berlin", locale="de-DE"),
                await authenticated(session),
                session,
            )
        async with session_factory() as verification_session:
            preferences: Final = await verification_session.get(UserPreferences, user_session.user_id)
            assert preferences is not None
            assert (preferences.timezone, preferences.locale) == ("Europe/Berlin", "de-DE")
            suggestion: Final = (
                await verification_session.execute(
                    text("SELECT id FROM regional_settings_suggestions WHERE session_id = :session_id"),
                    {"session_id": user_session.id},
                )
            ).first()
            assert suggestion is None

        # A differing report proposes a suggestion for both fields.
        async with session_factory() as session:
            await report_regional_settings(
                ReportedRegionalSettingsInputV1(timezone="America/New_York", locale="en-US"),
                await authenticated(session),
                session,
            )
        async with session_factory() as verification_session:
            pending: Final = (
                await verification_session.execute(
                    text(
                        "SELECT id, timezone, locale FROM regional_settings_suggestions WHERE session_id = :session_id"
                    ),
                    {"session_id": user_session.id},
                )
            ).one()
            suggestion_id: Final = pending.id
            assert (pending.timezone, pending.locale) == ("America/New_York", "en-US")

        # Accept the timezone, keep the locale.
        async with session_factory() as session:
            await decide_regional_settings_change(
                suggestion_id,
                RegionalSettingsDecisionInputV1(
                    timezone=RegionalSettingsDecision.ACCEPT,
                    locale=RegionalSettingsDecision.KEEP,
                ),
                await authenticated(session),
                session,
            )

        async with session_factory() as verification_session:
            decided_preferences: Final = await verification_session.get(UserPreferences, user_session.user_id)
            assert decided_preferences is not None
            assert (decided_preferences.timezone, decided_preferences.locale) == ("America/New_York", "de-DE")
            remaining_suggestion: Final = await verification_session.get(RegionalSettingsSuggestion, suggestion_id)
            assert remaining_suggestion is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_reported_regional_settings_columns_reject_partial_state(migrate_and_seed_database: str) -> None:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="constraint-check-token")

        async with session_factory() as session:
            with pytest.raises(IntegrityError, match='null value in column "locale".*reported_regional_settings'):
                _ = await session.execute(
                    text(
                        "INSERT INTO reported_regional_settings (session_id, timezone, reported_at) "
                        + "VALUES (:session_id, :timezone, now())",
                    ),
                    {"session_id": user_session.id, "timezone": "Europe/Berlin"},
                )
                await session.commit()
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_deleting_a_session_cascades_to_its_reported_settings(migrate_and_seed_database: str) -> None:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="cascade-delete-report-token")
        session_id: Final = user_session.id
        assert session_id is not None

        async with session_factory() as session:
            reported: Final = ReportedRegionalSettings(
                session_id=session_id,
                timezone="Europe/Berlin",
                locale="de-DE",
                reported_at=utc_now(),
            )
            session.add(reported)
            await session.commit()

        async with session_factory() as session:
            loaded_session: Final = await session.get(UserSession, session_id)
            assert loaded_session is not None
            await session.delete(loaded_session)
            await session.commit()

        async with session_factory() as verification_session:
            remaining: Final = await verification_session.get(ReportedRegionalSettings, session_id)
            assert remaining is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_deleting_a_session_cascades_to_its_suggestion(migrate_and_seed_database: str) -> None:
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="cascade-delete-token")
        session_id: Final = user_session.id
        assert session_id is not None

        async with session_factory() as session:
            suggestion: Final = RegionalSettingsSuggestion(session_id=session_id, timezone="Europe/Berlin")
            session.add(suggestion)
            await session.commit()
            suggestion_id: Final = suggestion.id

        async with session_factory() as session:
            loaded_session: Final = await session.get(UserSession, user_session.id)
            assert loaded_session is not None
            await session.delete(loaded_session)
            await session.commit()

        async with session_factory() as verification_session:
            remaining: Final = await verification_session.get(RegionalSettingsSuggestion, suggestion_id)
            assert remaining is None
    finally:
        await engine.dispose()


@pytest.mark.asyncio
async def test_traveling_device_does_not_repeatedly_prompt_and_resyncs_silently_on_return(
    migrate_and_seed_database: str,
) -> None:
    """A single session's timezone changes like a travelling laptop: home,
    then a differing location that gets dismissed, then back home again.
    Regression test for the two-device/travel concern in the design
    discussion: a dismissed suggestion must not reappear for a repeated
    report, and returning to a value that already matches the preference
    must resolve silently rather than re-prompting.
    """
    engine: Final = create_async_engine(migrate_and_seed_database, pool_pre_ping=True)
    session_factory: Final = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    try:
        user_session: Final = await _create_user_with_session(session_factory, token="travel-scenario-token")
        account: Final = Account(
            user_id=user_session.user_id,
            zitadel_user_id="travel-scenario-test",
            email="user@example.com",
            username="test-user",
        )

        async def authenticated(session: AsyncSession) -> AuthenticatedSession:
            loaded_session: Final = await session.get(UserSession, user_session.id)
            assert loaded_session is not None
            return AuthenticatedSession(account=account, session=loaded_session)

        async def report(timezone: str, locale: str) -> None:
            async with session_factory() as session:
                await report_regional_settings(
                    ReportedRegionalSettingsInputV1(timezone=timezone, locale=locale),
                    await authenticated(session),
                    session,
                )

        async def suggestion_for_session() -> Optional[RegionalSettingsSuggestion]:
            async with session_factory() as verification_session:
                return (
                    await verification_session.execute(
                        select(RegionalSettingsSuggestion).where(
                            RegionalSettingsSuggestion.session_id == user_session.id
                        )
                    )
                ).scalar_one_or_none()

        # At home: the first report confirms the preference; no suggestion.
        await report("Europe/Berlin", "de-DE")
        assert await suggestion_for_session() is None

        # Arrives in New York: differs from both the stored report and the
        # preference, so a suggestion appears.
        await report("America/New_York", "de-DE")
        pending: Final = await suggestion_for_session()
        assert pending is not None
        assert pending.timezone == "America/New_York"

        # Keep the home timezone.
        async with session_factory() as session:
            await decide_regional_settings_change(
                pending.id,
                RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.KEEP),
                await authenticated(session),
                session,
            )
        assert await suggestion_for_session() is None

        # Still in New York: an identical repeated report must not re-prompt.
        await report("America/New_York", "de-DE")
        assert await suggestion_for_session() is None

        # Back home: the report now matches the preference again, so it
        # resolves silently, without ever creating a new suggestion.
        await report("Europe/Berlin", "de-DE")
        assert await suggestion_for_session() is None

        async with session_factory() as verification_session:
            preferences: Final = await verification_session.get(UserPreferences, user_session.user_id)
            assert preferences is not None
            assert preferences.timezone == "Europe/Berlin"  # never moved
    finally:
        await engine.dispose()
