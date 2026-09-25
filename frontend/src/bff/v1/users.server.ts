import type { RequestEvent } from '@sveltejs/kit';

import { decideRegionalSettingsChangeV1 } from '$gen/sdk.gen';
import { reportRegionalSettingsV1 } from '$gen/sdk.gen';
import type { DecideRegionalSettingsChangeV1Error } from '$gen/types.gen';
import type { RegionalSettingsDecisionInputV1 } from '$gen/types.gen';
import type { ReportRegionalSettingsV1Error } from '$gen/types.gen';
import type { ReportedRegionalSettingsInputV1 } from '$gen/types.gen';

import { backendFetch } from '$bff/client';
import { logger } from '$logging';
import { backendCallCompleted } from '$logging/events.gen';

// A 401/409 here is an expected outcome the caller must translate into a
// response for the browser, not a backend failure—so these return a status
// rather than throwing.
export type BackendCallResult<TError> =
	{ ok: true } | { ok: false; status: number; error?: TError };

export async function reportRegionalSettings(
	event: RequestEvent,
	body: ReportedRegionalSettingsInputV1
): Promise<BackendCallResult<ReportRegionalSettingsV1Error>> {
	const start = performance.now();
	const { error, response } = await reportRegionalSettingsV1({ fetch: backendFetch(event), body });
	logger.info(
		backendCallCompleted({
			operation_id: 'reportRegionalSettingsV1',
			status_code: response?.status ?? 0,
			duration_ms: Math.round((performance.now() - start) * 100) / 100
		})
	);

	if (error) {
		return { ok: false, status: response?.status ?? 500, error };
	}
	return { ok: true };
}

export async function decideRegionalSettingsChange(
	event: RequestEvent,
	suggestionId: string,
	body: RegionalSettingsDecisionInputV1
): Promise<BackendCallResult<DecideRegionalSettingsChangeV1Error>> {
	const start = performance.now();
	const { error, response } = await decideRegionalSettingsChangeV1({
		fetch: backendFetch(event),
		path: { suggestion_id: suggestionId },
		body
	});
	logger.info(
		backendCallCompleted({
			operation_id: 'decideRegionalSettingsChangeV1',
			status_code: response?.status ?? 0,
			duration_ms: Math.round((performance.now() - start) * 100) / 100
		})
	);

	if (error) {
		return { ok: false, status: response?.status ?? 500, error };
	}
	return { ok: true };
}
