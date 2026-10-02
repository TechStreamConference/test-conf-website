from datetime import timedelta
from typing import Final
from typing import Optional
from unittest.mock import AsyncMock
from unittest.mock import Mock
from uuid import UUID
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import backend.routes.v1.users as users_module
from backend.logging.events_gen import RegionalSettingsReportProcessed
from backend.models.requests import RegionalSettingsDecision
from backend.models.requests import RegionalSettingsDecisionInputV1
from backend.models.requests import ReportedRegionalSettingsInputV1
from backend.models.requests import UserPreferencesInputV1
from backend.models.tables import Account
from backend.models.tables import RegionalSettingsSuggestion
from backend.models.tables import ReportedRegionalSettings
from backend.models.tables import UserPreferences
from backend.models.tables import UserSession
from backend.routes.v1.users import decide_regional_settings_change
from backend.routes.v1.users import report_regional_settings
from backend.routes.v1.users import update_preferences
from backend.session import AuthenticatedSession
from backend.utils import utc_now


def _authenticated(*, user_id: int = 42, session_id: int = 1) -> AuthenticatedSession:
    now: Final = utc_now()
    account: Final = Account(
        user_id=user_id,
        zitadel_user_id="provider-user",
        email="user@example.com",
        username="test-user",
    )
    user_session: Final = UserSession(
        id=session_id,
        user_id=user_id,
        token_hash="hashed-token",
        expires_at=now + timedelta(days=1),
        absolute_expires_at=now + timedelta(days=30),
    )
    return AuthenticatedSession(account=account, session=user_session)


def _locked_session(*, session_id: int = 1) -> UserSession:
    now: Final = utc_now()
    return UserSession(
        id=session_id,
        user_id=42,
        token_hash="hashed-token",
        expires_at=now + timedelta(days=1),
        absolute_expires_at=now + timedelta(days=30),
    )


def _reported(*, session_id: int = 1, timezone: str, locale: str) -> ReportedRegionalSettings:
    return ReportedRegionalSettings(session_id=session_id, timezone=timezone, locale=locale, reported_at=utc_now())


def _captured_log(monkeypatch: pytest.MonkeyPatch) -> Mock:
    logged: Final = Mock()
    monkeypatch.setattr(users_module.logging, "info", logged)
    return logged


def _result(*, scalar_one: object = None, scalar_one_or_none: object = None) -> Mock:
    return Mock(scalar_one=Mock(return_value=scalar_one), scalar_one_or_none=Mock(return_value=scalar_one_or_none))


def _session(*execute_results: Mock, get_results: tuple[object, ...] = ()) -> Mock:
    session: Final = Mock(spec=AsyncSession)
    session.execute = AsyncMock(side_effect=list(execute_results))
    session.get = AsyncMock(side_effect=list(get_results)) if get_results else AsyncMock(return_value=None)
    session.delete = AsyncMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


def _executed_statement_params(session: Mock, *, call_index: int) -> dict[str, object]:
    statement = session.execute.await_args_list[call_index].args[0]
    return statement.compile().params


@pytest.mark.asyncio
async def test_manual_preference_update_replaces_existing_values() -> None:
    stored: Final = UserPreferences(user_id=42, timezone="America/New_York", locale="haw")
    session: Final = _session(
        _result(scalar_one=stored),
        _result(scalar_one_or_none=None),
    )
    preferences: Final = UserPreferencesInputV1(timezone="America/New_York", locale="haw")

    result: Final = await update_preferences(preferences, _authenticated(), session)  # type: ignore[arg-type]

    assert result.model_dump() == {"timezone": "America/New_York", "locale": "haw"}
    statement: Final = session.execute.await_args_list[0].args[0]
    sql: Final = str(statement)
    assert "coalesce" not in sql.lower()
    assert "ON CONFLICT" in sql
    assert _executed_statement_params(session, call_index=0) == {
        "user_id": 42,
        "timezone": "America/New_York",
        "locale": "haw",
    }
    session.delete.assert_not_awaited()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_manual_preference_update_clears_pending_suggestion_for_current_session() -> None:
    stored: Final = UserPreferences(user_id=42, timezone="America/New_York", locale="haw")
    pending: Final = RegionalSettingsSuggestion(session_id=1, timezone="Europe/Berlin", locale=None)
    session: Final = _session(
        _result(scalar_one=stored),
        _result(scalar_one_or_none=pending),
    )
    preferences: Final = UserPreferencesInputV1(timezone="America/New_York", locale="haw")

    _ = await update_preferences(preferences, _authenticated(), session)  # type: ignore[arg-type]

    session.delete.assert_awaited_once_with(pending)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_report_initializes_missing_preference_and_does_not_create_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: Final = _captured_log(monkeypatch)
    locked_session: Final = _locked_session()
    session: Final = _session(
        _result(scalar_one=locked_session),
        _result(scalar_one_or_none=None),
        Mock(),  # preferences upsert result is discarded
        Mock(),  # report upsert result is discarded
        get_results=(None, None),  # no preferences row and no previous report yet
    )
    report: Final = ReportedRegionalSettingsInputV1(timezone="Europe/Berlin", locale="de-DE")

    await report_regional_settings(report, _authenticated(), session)  # type: ignore[arg-type]

    preferences_upsert: Final = session.execute.await_args_list[2].args[0]
    assert "ON CONFLICT (user_id) DO NOTHING" in str(preferences_upsert)
    assert _executed_statement_params(session, call_index=2) == {
        "user_id": 42,
        "timezone": "Europe/Berlin",
        "locale": "de-DE",
    }
    report_upsert_params: Final = _executed_statement_params(session, call_index=3)
    assert report_upsert_params["session_id"] == 1
    assert report_upsert_params["timezone"] == "Europe/Berlin"
    assert report_upsert_params["locale"] == "de-DE"
    assert report_upsert_params["reported_at"] is not None
    session.delete.assert_not_awaited()
    added_suggestions: Final = [
        call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], RegionalSettingsSuggestion)
    ]
    assert added_suggestions == []
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
    logged_event: Final = logged.call_args.args[0]
    assert isinstance(logged_event, RegionalSettingsReportProcessed)
    assert logged_event.session_id == 1
    assert not logged_event.is_no_op
    assert logged_event.timezone_outcome == "initialized"
    assert logged_event.locale_outcome == "initialized"


@pytest.mark.asyncio
async def test_repeated_equivalent_report_is_a_no_op(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: Final = _captured_log(monkeypatch)
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    previous_report: Final = _reported(timezone="Europe/Berlin", locale="de-de")
    locked_session: Final = _locked_session()
    session: Final = _session(
        _result(scalar_one=locked_session),
        _result(scalar_one_or_none=None),
        get_results=(preferences, previous_report),
    )
    report: Final = ReportedRegionalSettingsInputV1(timezone="Europe/Berlin", locale="de-DE")

    await report_regional_settings(report, _authenticated(), session)  # type: ignore[arg-type]

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()
    session.add.assert_not_called()
    session.delete.assert_not_awaited()
    # No upsert is issued for a no-op report.
    assert session.execute.await_count == 2
    logged_event: Final = logged.call_args.args[0]
    assert isinstance(logged_event, RegionalSettingsReportProcessed)
    assert logged_event.is_no_op
    assert logged_event.timezone_outcome is None
    assert logged_event.locale_outcome is None


@pytest.mark.asyncio
async def test_report_differing_from_preference_creates_pending_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: Final = _captured_log(monkeypatch)
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    locked_session: Final = _locked_session()
    session: Final = _session(
        _result(scalar_one=locked_session),
        _result(scalar_one_or_none=None),
        Mock(),
        Mock(),
        get_results=(preferences, None),
    )
    report: Final = ReportedRegionalSettingsInputV1(timezone="America/New_York", locale="en-US")

    await report_regional_settings(report, _authenticated(), session)  # type: ignore[arg-type]

    # The row already exists, so "do nothing on conflict" leaves the
    # preference untouched; verified for real against Postgres in the
    # integration tests. Here we confirm the reported values were sent.
    assert _executed_statement_params(session, call_index=2) == {
        "user_id": 42,
        "timezone": "America/New_York",
        "locale": "en-US",
    }
    report_upsert_params: Final = _executed_statement_params(session, call_index=3)
    assert report_upsert_params["timezone"] == "America/New_York"
    assert report_upsert_params["locale"] == "en-US"
    added_suggestions: Final = [
        call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], RegionalSettingsSuggestion)
    ]
    assert len(added_suggestions) == 1
    assert added_suggestions[0].session_id == 1
    assert added_suggestions[0].timezone == "America/New_York"
    assert added_suggestions[0].locale == "en-US"
    session.commit.assert_awaited_once()
    logged_event: Final = logged.call_args.args[0]
    assert logged_event.timezone_outcome == "suggestion_created"
    assert logged_event.locale_outcome == "suggestion_created"


@pytest.mark.asyncio
async def test_report_matching_preference_again_clears_pending_suggestion(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    logged: Final = _captured_log(monkeypatch)
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    previous_report: Final = _reported(timezone="America/New_York", locale="de-DE")
    locked_session: Final = _locked_session()
    pending: Final = RegionalSettingsSuggestion(session_id=1, timezone="America/New_York", locale=None)
    session: Final = _session(
        _result(scalar_one=locked_session),
        _result(scalar_one_or_none=pending),
        Mock(),
        Mock(),
        get_results=(preferences, previous_report),
    )
    report: Final = ReportedRegionalSettingsInputV1(timezone="Europe/Berlin", locale="de-DE")

    await report_regional_settings(report, _authenticated(), session)  # type: ignore[arg-type]

    session.delete.assert_awaited_once_with(pending)
    added_suggestions: Final = [
        call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], RegionalSettingsSuggestion)
    ]
    assert added_suggestions == []
    session.commit.assert_awaited_once()
    logged_event: Final = logged.call_args.args[0]
    assert logged_event.timezone_outcome == "suggestion_cleared"
    assert logged_event.locale_outcome == "unchanged"


@pytest.mark.asyncio
async def test_newer_differing_report_replaces_pending_suggestion(monkeypatch: pytest.MonkeyPatch) -> None:
    logged: Final = _captured_log(monkeypatch)
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    previous_report: Final = _reported(timezone="America/New_York", locale="de-DE")
    locked_session: Final = _locked_session()
    pending: Final = RegionalSettingsSuggestion(session_id=1, timezone="America/New_York", locale=None)
    session: Final = _session(
        _result(scalar_one=locked_session),
        _result(scalar_one_or_none=pending),
        Mock(),
        Mock(),
        get_results=(preferences, previous_report),
    )
    report: Final = ReportedRegionalSettingsInputV1(timezone="Asia/Tokyo", locale="de-DE")

    await report_regional_settings(report, _authenticated(), session)  # type: ignore[arg-type]

    session.delete.assert_awaited_once_with(pending)
    session.flush.assert_awaited_once()
    added_suggestions: Final = [
        call.args[0] for call in session.add.call_args_list if isinstance(call.args[0], RegionalSettingsSuggestion)
    ]
    assert len(added_suggestions) == 1
    assert added_suggestions[0].timezone == "Asia/Tokyo"
    session.commit.assert_awaited_once()
    logged_event: Final = logged.call_args.args[0]
    assert logged_event.timezone_outcome == "suggestion_replaced"
    assert logged_event.locale_outcome == "unchanged"


def _suggestion(
    *,
    suggestion_id: Optional[UUID] = None,
    session_id: int = 1,
    timezone: Optional[str] = None,
    locale: Optional[str] = None,
) -> RegionalSettingsSuggestion:
    return RegionalSettingsSuggestion(
        id=suggestion_id if suggestion_id is not None else uuid4(),
        session_id=session_id,
        timezone=timezone,
        locale=locale,
    )


@pytest.mark.asyncio
async def test_accepting_a_decision_updates_the_preference_and_resolves_the_field() -> None:
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    pending: Final = _suggestion(timezone="America/New_York")
    session: Final = _session()
    session.get = AsyncMock(side_effect=[pending, preferences])
    decision: Final = RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.ACCEPT)

    await decide_regional_settings_change(pending.id, decision, _authenticated(), session)  # type: ignore[arg-type]

    assert preferences.timezone == "America/New_York"
    session.delete.assert_awaited_once_with(pending)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_keeping_a_decision_does_not_change_the_preference() -> None:
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    pending: Final = _suggestion(timezone="America/New_York")
    session: Final = _session()
    session.get = AsyncMock(side_effect=[pending, preferences])
    decision: Final = RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.KEEP)

    await decide_regional_settings_change(pending.id, decision, _authenticated(), session)  # type: ignore[arg-type]

    assert preferences.timezone == "Europe/Berlin"
    session.delete.assert_awaited_once_with(pending)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_deciding_one_field_leaves_the_other_pending() -> None:
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    pending: Final = _suggestion(timezone="America/New_York", locale="en-US")
    session: Final = _session()
    session.get = AsyncMock(side_effect=[pending, preferences])
    decision: Final = RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.ACCEPT)

    await decide_regional_settings_change(pending.id, decision, _authenticated(), session)  # type: ignore[arg-type]

    assert preferences.timezone == "America/New_York"
    assert preferences.locale == "de-DE"
    assert pending.timezone is None
    assert pending.locale == "en-US"
    session.delete.assert_not_awaited()
    session.add.assert_any_call(pending)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_deciding_both_fields_resolves_the_suggestion() -> None:
    preferences: Final = UserPreferences(user_id=42, timezone="Europe/Berlin", locale="de-DE")
    pending: Final = _suggestion(timezone="America/New_York", locale="en-US")
    session: Final = _session()
    session.get = AsyncMock(side_effect=[pending, preferences])
    decision: Final = RegionalSettingsDecisionInputV1(
        timezone=RegionalSettingsDecision.ACCEPT,
        locale=RegionalSettingsDecision.KEEP,
    )

    await decide_regional_settings_change(pending.id, decision, _authenticated(), session)  # type: ignore[arg-type]

    assert preferences.timezone == "America/New_York"
    assert preferences.locale == "de-DE"
    session.delete.assert_awaited_once_with(pending)
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_unknown_suggestion_id_returns_conflict() -> None:
    session: Final = _session()
    decision: Final = RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.ACCEPT)

    with pytest.raises(HTTPException) as exc_info:
        _ = await decide_regional_settings_change(uuid4(), decision, _authenticated(), session)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_suggestion_from_another_session_returns_conflict() -> None:
    pending: Final = _suggestion(session_id=99, timezone="America/New_York")
    session: Final = _session()
    session.get = AsyncMock(return_value=pending)
    decision: Final = RegionalSettingsDecisionInputV1(timezone=RegionalSettingsDecision.ACCEPT)

    with pytest.raises(HTTPException) as exc_info:
        _ = await decide_regional_settings_change(pending.id, decision, _authenticated(session_id=1), session)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_deciding_a_field_without_a_pending_candidate_returns_conflict() -> None:
    pending: Final = _suggestion(timezone="America/New_York", locale=None)
    session: Final = _session()
    session.get = AsyncMock(return_value=pending)
    decision: Final = RegionalSettingsDecisionInputV1(locale=RegionalSettingsDecision.ACCEPT)

    with pytest.raises(HTTPException) as exc_info:
        _ = await decide_regional_settings_change(pending.id, decision, _authenticated(), session)  # type: ignore[arg-type]

    assert exc_info.value.status_code == 409
    session.commit.assert_not_awaited()
