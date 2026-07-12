import type { PageServerLoad } from './$types';

import { loadGlobals } from '$bff/v1/globals.server';

export const load: PageServerLoad = async (event) => {
	return {
		globals: await loadGlobals(event)
	}
}
