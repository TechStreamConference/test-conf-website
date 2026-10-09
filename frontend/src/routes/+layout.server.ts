import { loadGlobals } from '$bff/v1/globals.server';

import { UserState } from '$lib/helper/menus';

import type { LayoutServerLoad } from './$types';

export const load: LayoutServerLoad = async (event) => {
    const globals = await loadGlobals(event);

    return {
        // Placeholders until the language and the logged-in state come from the backend.
        languageTag: 'en',
        userState: UserState.LoggedOut,
        footerText: globals.footerText
    };
};
