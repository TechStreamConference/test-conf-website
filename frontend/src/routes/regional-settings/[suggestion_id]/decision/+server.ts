import { json } from '@sveltejs/kit';

import { decideRegionalSettingsChange } from '$bff/v1/users.server';
import type { RegionalSettingsDecisionInputV1 } from '$gen/types.gen';

import type { RequestHandler } from './$types';

export const PUT: RequestHandler = async (event) => {
	const body = (await event.request.json()) as RegionalSettingsDecisionInputV1;
	const result = await decideRegionalSettingsChange(event, event.params.suggestion_id, body);
	if (!result.ok) {
		return json(result.error ?? null, { status: result.status });
	}
	return new Response(null, { status: 204 });
};
