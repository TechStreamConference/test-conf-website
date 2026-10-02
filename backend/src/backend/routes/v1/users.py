from typing import Annotated
from typing import Final
from uuid import UUID

from fastapi import APIRouter
from fastapi import Depends
from fastapi import status
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import col
from sqlmodel import select

from backend import logging
from backend.database import get_session
from backend.logging.events_gen import RegionalSettingsReportProcessed
from backend.models.requests import RegionalSettingsDecision
from backend.models.requests import RegionalSettingsDecisionInputV1
from backend.models.requests import ReportedRegionalSettingsInputV1
from backend.models.requests import UserPreferencesInputV1
from backend.models.responses import NotAuthenticatedResponseV1
from backend.models.responses import RegionalSettingsChangeConflictResponseV1
from backend.models.responses import UserPreferencesResponseV1
from backend.models.tables import RegionalSettingsSuggestion
from backend.models.tables import ReportedRegionalSettings
from backend.models.tables import UserPreferences
from backend.models.tables import UserSession
from backend.session import AuthenticatedSession
from backend.session import get_current_user
from backend.user_preferences import categorize_field_outcome
from backend.user_preferences import process_regional_settings_report
from backend.utils import create_http_exception
from backend.utils import utc_now

ROUTER = APIRouter(prefix="/users/me")


@ROUTER.put(
    "/preferences",
    summary="Update current-user preferences",
    description="Replaces the current user's timezone and locale preferences.",
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": NotAuthenticatedResponseV1}},
    operation_id="update current user preferences v1",
)
async def update_preferences(
    preferences: UserPreferencesInputV1,
    authenticated: Annotated[AuthenticatedSession, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> UserPreferencesResponseV1:
    # An explicit replace, so an upsert: the row may not exist yet if this is
    # the first preference ever confirmed for this user.
    upsert: Final = pg_insert(UserPreferences).values(
        user_id=authenticated.account.user_id,
        timezone=preferences.timezone,
        locale=preferences.locale,
    )
    statement: Final = upsert.on_conflict_do_update(
        index_elements=[col(UserPreferences.user_id)],
        set_={"timezone": upsert.excluded.timezone, "locale": upsert.excluded.locale},
    ).returning(UserPreferences)
    stored: Final = (await session.execute(statement)).scalar_one()

    # An explicit choice acknowledges the current report: it replaces any
    # pending suggestion for this session rather than leaving it to be
    # re-proposed by the next report.
    existing_suggestion: Final = (
        await session.execute(
            select(RegionalSettingsSuggestion).where(RegionalSettingsSuggestion.session_id == authenticated.session.id)
        )
    ).scalar_one_or_none()
    if existing_suggestion is not None:
        await session.delete(existing_suggestion)

    await session.commit()
    return UserPreferencesResponseV1(timezone=stored.timezone, locale=stored.locale)


@ROUTER.put(
    "/reported-regional-settings",
    summary="Report the current session's regional settings",
    description=(
        "Records the browser-reported timezone and locale for the current application session. "
        + "Initializes a missing preference, proposes a suggestion when the report differs from an "
        + "existing preference, or is a no-op when the report is equivalent to what was last reported."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={status.HTTP_401_UNAUTHORIZED: {"model": NotAuthenticatedResponseV1}},
    operation_id="report regional settings v1",
)
async def report_regional_settings(
    report: ReportedRegionalSettingsInputV1,
    authenticated: Annotated[AuthenticatedSession, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    session_id: Final = authenticated.session.id
    if session_id is None:
        raise RuntimeError("Authenticated session has no id.")

    # Lock the session row so concurrent reports for the same session are
    # serialized; the last committed report becomes authoritative. We lock
    # this row on purpose even though this endpoint no longer stores data on
    # it directly: the session row is guaranteed to already exist (unlike the
    # rows below, which may not), so it is the natural mutex for them.
    _ = (await session.execute(select(UserSession).where(UserSession.id == session_id).with_for_update())).scalar_one()

    # No row means no preference has ever been confirmed yet.
    preferences: Final = await session.get(UserPreferences, authenticated.account.user_id)
    preference_timezone: Final = preferences.timezone if preferences is not None else None
    preference_locale: Final = preferences.locale if preferences is not None else None

    # No row means no report exists yet for this session.
    previous_report: Final = await session.get(ReportedRegionalSettings, session_id)
    previous_reported_timezone: Final = previous_report.timezone if previous_report is not None else None
    previous_reported_locale: Final = previous_report.locale if previous_report is not None else None

    existing_suggestion: Final = (
        await session.execute(
            select(RegionalSettingsSuggestion).where(RegionalSettingsSuggestion.session_id == session_id)
        )
    ).scalar_one_or_none()

    outcome: Final = process_regional_settings_report(
        reported_timezone=report.timezone,
        reported_locale=report.locale,
        previous_reported_timezone=previous_reported_timezone,
        previous_reported_locale=previous_reported_locale,
        preference_timezone=preference_timezone,
        preference_locale=preference_locale,
        suggested_timezone=existing_suggestion.timezone if existing_suggestion is not None else None,
        suggested_locale=existing_suggestion.locale if existing_suggestion is not None else None,
    )

    if outcome.is_no_op:
        # Nothing changed: release the row lock without writing anything.
        await session.rollback()
        logging.info(RegionalSettingsReportProcessed(session_id=session_id, is_no_op=True))
        return

    timezone_category: Final = categorize_field_outcome(
        preference_was_missing=preference_timezone is None,
        previous_suggestion=existing_suggestion.timezone if existing_suggestion is not None else None,
        new_suggestion=outcome.timezone.suggestion,
    )
    locale_category: Final = categorize_field_outcome(
        preference_was_missing=preference_locale is None,
        previous_suggestion=existing_suggestion.locale if existing_suggestion is not None else None,
        new_suggestion=outcome.locale.suggestion,
    )

    # Set-if-unset, as an upsert: the row may not exist yet. Once it exists,
    # both fields are always set (see `UserPreferences`), so a report can only
    # ever initialize the row, never change an existing preference; "do
    # nothing on conflict" is therefore both correct and atomic/race-safe
    # against a concurrent report for a *different* session of the same user.
    preferences_upsert: Final = pg_insert(UserPreferences).values(
        user_id=authenticated.account.user_id,
        timezone=report.timezone,
        locale=report.locale,
    )
    _ = await session.execute(preferences_upsert.on_conflict_do_nothing(index_elements=[col(UserPreferences.user_id)]))

    # Unlike the confirmed preference, the latest report is always replaced.
    report_upsert: Final = pg_insert(ReportedRegionalSettings).values(
        session_id=session_id,
        timezone=report.timezone,
        locale=report.locale,
        reported_at=utc_now(),
    )
    _ = await session.execute(
        report_upsert.on_conflict_do_update(
            index_elements=[col(ReportedRegionalSettings.session_id)],
            set_={
                "timezone": report_upsert.excluded.timezone,
                "locale": report_upsert.excluded.locale,
                "reported_at": report_upsert.excluded.reported_at,
            },
        )
    )

    new_suggestion_content: Final = (outcome.timezone.suggestion, outcome.locale.suggestion)
    old_suggestion_content: Final = (
        (
            existing_suggestion.timezone,
            existing_suggestion.locale,
        )
        if existing_suggestion is not None
        else (None, None)
    )
    if new_suggestion_content != old_suggestion_content:
        if existing_suggestion is not None:
            await session.delete(existing_suggestion)
            await session.flush()
        if new_suggestion_content != (None, None):
            session.add(
                RegionalSettingsSuggestion(
                    session_id=session_id,
                    timezone=outcome.timezone.suggestion,
                    locale=outcome.locale.suggestion,
                )
            )

    await session.commit()
    logging.info(
        RegionalSettingsReportProcessed(
            session_id=session_id,
            is_no_op=False,
            timezone_outcome=timezone_category,
            locale_outcome=locale_category,
        )
    )


@ROUTER.put(
    "/regional-settings-changes/{suggestion_id}/decision",
    summary="Decide a pending regional settings change",
    description=(
        "Accepts or keeps the current session's pending timezone and/or locale suggestion, "
        + "independently per field. Each decided field must have a pending candidate in the "
        + "referenced suggestion."
    ),
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        status.HTTP_401_UNAUTHORIZED: {"model": NotAuthenticatedResponseV1},
        status.HTTP_409_CONFLICT: {"model": RegionalSettingsChangeConflictResponseV1},
    },
    operation_id="decide regional settings change v1",
)
async def decide_regional_settings_change(
    suggestion_id: UUID,
    decision: RegionalSettingsDecisionInputV1,
    authenticated: Annotated[AuthenticatedSession, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> None:
    suggestion: Final = await session.get(RegionalSettingsSuggestion, suggestion_id)

    # An unknown, superseded, or cross-session ID is reported identically so
    # the endpoint never reveals whether an ID belongs to another session. A
    # field decided without a pending candidate is rejected the same way.
    if (
        suggestion is None
        or suggestion.session_id != authenticated.session.id
        or (decision.timezone is not None and suggestion.timezone is None)
        or (decision.locale is not None and suggestion.locale is None)
    ):
        raise create_http_exception(status.HTTP_409_CONFLICT, RegionalSettingsChangeConflictResponseV1())

    # A suggestion only ever exists for a field whose preference is already
    # confirmed (see the state machine), so this row is guaranteed to exist.
    preferences: Final = await session.get(UserPreferences, authenticated.account.user_id)
    if preferences is None:
        raise RuntimeError("Suggestion exists without a corresponding confirmed preference.")

    if decision.timezone is not None:
        if decision.timezone == RegionalSettingsDecision.ACCEPT:
            # Guaranteed non-null: the conflict check above rejected deciding
            # a field with no pending candidate.
            if suggestion.timezone is None:
                raise RuntimeError("Suggestion has no pending timezone despite passing validation.")
            preferences.timezone = suggestion.timezone
        suggestion.timezone = None

    if decision.locale is not None:
        if decision.locale == RegionalSettingsDecision.ACCEPT:
            if suggestion.locale is None:
                raise RuntimeError("Suggestion has no pending locale despite passing validation.")
            preferences.locale = suggestion.locale
        suggestion.locale = None

    session.add(preferences)
    if suggestion.timezone is None and suggestion.locale is None:
        await session.delete(suggestion)
    else:
        session.add(suggestion)

    await session.commit()
