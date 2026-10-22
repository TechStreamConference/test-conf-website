import type { MeResponseV1 } from '$gen/types.gen';
import type { RegionalSettingsChangeV1 } from '$gen/types.gen';
import type { RegionalSettingsDecisionInputV1 } from '$gen/types.gen';
import type { RegionalSettingsV1 } from '$gen/types.gen';
import type { ReportedRegionalSettingsInputV1 } from '$gen/types.gen';

// The backend rejects longer locales.
const MAX_LOCALE_LENGTH = 64;

export type PendingRegionalSettingsChange = {
    change: RegionalSettingsChangeV1;
    // A suggestion can only exist for a field that already has a confirmed
    // preference (see the state machine in the design doc), so this is always
    // present alongside `change`.
    current: RegionalSettingsV1;
};

// These calls go through this app’s own `/regional-settings` routes (the
// BFF), which forward to the backend server-side, same as every other
// backend call in this app — not directly from the browser.

async function fetch_me(): Promise<MeResponseV1 | undefined> {
    const response = await fetch('/regional-settings', { credentials: 'same-origin' });
    if (!response.ok) {
        return undefined;
    }
    return (await response.json()) as MeResponseV1;
}

/**
 * @brief Turns the browser’s language into a locale the backend accepts. The browser’s
 * language list can be customized (e.g. Firefox’s `intl.accept_languages`), so it may contain
 * a malformed tag such as `en_US`, which would make the backend reject the whole report,
 * including the timezone. A well-formed language is canonicalized, since the backend compares
 * locales without canonicalizing them. A malformed or overlong one is replaced with the locale
 * the browser resolves for formatting, which is always valid. The backend stays the authority
 * on which locales are valid; this only avoids reporting one it would reject.
 * @param language the browser’s language, e.g. `navigator.language`.
 * @returns the canonical language, or the browser’s resolved locale as a fallback.
 */
export function toReportableLocale(language: string): string {
    try {
        const [canonical] = Intl.getCanonicalLocales(language);
        if (canonical !== undefined && canonical.length <= MAX_LOCALE_LENGTH) {
            return canonical;
        }
    } catch (error) {
        if (!(error instanceof RangeError)) {
            throw error;
        }
    }
    return Intl.DateTimeFormat().resolvedOptions().locale;
}

async function report_browser_regional_settings(): Promise<void> {
    const body: ReportedRegionalSettingsInputV1 = {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
        locale: toReportableLocale(navigator.language)
    };
    await fetch('/regional-settings', {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
    });
}

/**
 * Reports the browser’s current timezone and locale for this application
 * session and returns any resulting pending suggestion together with the
 * current confirmed preferences, or `undefined` when there is no
 * authenticated session or nothing is pending.
 */
export async function init_regional_settings(): Promise<PendingRegionalSettingsChange | undefined> {
    if ((await fetch_me()) == undefined) {
        return undefined;
    }

    await report_browser_regional_settings();

    const me = await fetch_me();
    if (me?.regionalSettingsChange == undefined || me.regionalSettings == undefined) {
        return undefined;
    }

    return { change: me.regionalSettingsChange, current: me.regionalSettings };
}

export async function decide_regional_settings_change(
    suggestion_id: string,
    decision: RegionalSettingsDecisionInputV1
): Promise<void> {
    await fetch(`/regional-settings/${suggestion_id}/decision`, {
        method: 'PUT',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(decision)
    });
}
