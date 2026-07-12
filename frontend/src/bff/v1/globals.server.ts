import type { RequestEvent } from '@sveltejs/kit';

import { getGlobalsV1 } from '$gen/sdk.gen';
import type { GlobalsResponseV1 } from '$gen/types.gen';

import '$bff/client';
import { UndefinedDataError } from '$bff/errors';
import { GenericBackendError } from '$bff/errors';

export async function loadGlobals(fetch: RequestEvent['fetch']): Promise<GlobalsResponseV1> {
	const { data, error } = await getGlobalsV1({ fetch });

	if (error) {
		throw new GenericBackendError('loadGlobals', error);
	}

	if (data == undefined) {
		throw new UndefinedDataError('loadGlobals');
	}

	return data;
}
