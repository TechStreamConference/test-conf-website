import { getCurrentUser } from '$bff/v1/auth.server';
import { loadGlobals } from '$bff/v1/globals.server';
import { GenericBackendError } from '$bff/errors';

import { UserState } from '$lib/helper/menus';

import type { LayoutServerLoad } from './$types';

const HTTP_UNAUTHORIZED = 401;

export const load: LayoutServerLoad = async (event) => {
    const [globals, user] = await Promise.all([loadGlobals(event), getCurrentUser(event)]);

    // A 401 only means that nobody is logged in. Every other failure is a real backend error.
    if (!user.ok && user.status !== HTTP_UNAUTHORIZED) {
        throw new GenericBackendError('getCurrentUser', user.status);
    }

    return {
        // Placeholder until the language comes from the backend.
        languageTag: 'en',
        userState: user.ok ? UserState.LoggedIn : UserState.LoggedOut,
        user: user.ok ? user.data : null,
        footerText: globals.footerText
    };
};
