import '$bff/client';

import { getGlobalsV1 } from '$gen/sdk.gen';
import type { GlobalsResponseV1 } from '$gen/types.gen';
import { UndefinedDataError } from '$bff/errors';
import { GenericBackendError } from '$bff/errors';

export async function loadGlobals(): Promise<GlobalsResponseV1> {
	const { data, error } = await getGlobalsV1();

	if (error) {
		throw new GenericBackendError('loadGlibals', error);
	}

	if (data == undefined) {
		throw new UndefinedDataError('loadGlobals');
	}

	return data;
}
