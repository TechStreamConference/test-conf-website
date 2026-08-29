import type { RequestEvent } from '@sveltejs/kit';

import type { GlobalsResponseV1 } from '$gen/types.gen';
import { UndefinedDataError } from '$bff/errors';
import { GenericBackendError } from '$bff/errors';
import { getGlobalsV1 } from '$gen/sdk.gen';
import { logger } from '$logging';
import { backendCallCompleted } from '$logging/events.gen';

export async function loadGlobals(event: RequestEvent): Promise<GlobalsResponseV1> {
	const start = performance.now();
	const { data, error, response } = await getGlobalsV1({ fetch: event.fetch });
	logger.info(
		backendCallCompleted({
			operation_id: 'getGlobalsV1',
			status_code: response?.status ?? 0,
			duration_ms: Math.round((performance.now() - start) * 100) / 100
		})
	);

	if (error) {
		throw new GenericBackendError('loadGlobals', error);
	}

	if (data == undefined) {
		throw new UndefinedDataError('loadGlobals');
	}

	return data;
}
