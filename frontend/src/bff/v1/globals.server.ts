import type { RequestEvent } from '@sveltejs/kit';

import { getGlobalsV1 } from '$gen/sdk.gen';
import type { GlobalsResponseV1 } from '$gen/types.gen';

import { UndefinedDataError } from '$bff/errors';
import { GenericBackendError } from '$bff/errors';

export async function loadGlobals(event: RequestEvent): Promise<GlobalsResponseV1> {
	const { data, error } = await getGlobalsV1({ fetch: event.fetch });

	if (error) {
		console.log(error);
		throw new GenericBackendError('loadGlobals', error);
	}

	if (data == undefined) {
		throw new UndefinedDataError('loadGlobals');
	}

	return data;
}
