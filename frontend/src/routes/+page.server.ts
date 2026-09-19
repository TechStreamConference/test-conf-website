import { loadGlobals } from '$bff/v1/globals.server';

import type { PageServerLoad } from './$types';

export const load: PageServerLoad = async (event) => {
    return {
        globals: await loadGlobals(event)
    };
};
