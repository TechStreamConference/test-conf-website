import type { MeResponseV1 } from '$gen/types.gen';
import type { RegionalSettingsChangeV1 } from '$gen/types.gen';
import type { RegionalSettingsDecisionInputV1 } from '$gen/types.gen';
import type { RegionalSettingsV1 } from '$gen/types.gen';
import type { ReportedRegionalSettingsInputV1 } from '$gen/types.gen';

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

async function report_browser_regional_settings(): Promise<void> {
	const body: ReportedRegionalSettingsInputV1 = {
		timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
		locale: navigator.language
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
	if (me?.regional_settings_change == undefined || me.regional_settings == undefined) {
		return undefined;
	}

	return { change: me.regional_settings_change, current: me.regional_settings };
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
