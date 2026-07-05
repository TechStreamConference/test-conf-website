import '$bff/client';

import { getGlobalsV1 } from '$gen/sdk.gen';
import type { GlobalsResponseV1 } from '$gen/types.gen';

export async function loadGlobals(): Promise<GlobalsResponseV1> {
	const { data, error } = await getGlobalsV1();

	if (error || data == undefined) {
		throw error;
	}

	return data;
}
