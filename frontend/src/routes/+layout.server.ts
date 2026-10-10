import { getCurrentUser } from '$bff/v1/auth.server';
import { loadGlobals } from '$bff/v1/globals.server';
import { GenericBackendError } from '$bff/errors';

import { DEFAULT_LANGUAGE_TAG } from '$lib/helper/language';
import { withLanguage } from '$lib/helper/language';
import { UserState } from '$lib/helper/menus';

import type { LayoutServerLoad } from './$types';

const HTTP_UNAUTHORIZED = 401;

export const load: LayoutServerLoad = async (event) => {
    const [globals, user] = await Promise.all([loadGlobals(event), getCurrentUser(event)]);

    // A 401 only means that nobody is logged in. Every other failure is a real backend error.
    if (!user.ok && user.status !== HTTP_UNAUTHORIZED) {
        throw new GenericBackendError('getCurrentUser', user.status);
    }

    // The default language, until the language comes from the backend. A page can override it with `withLanguage`.
    return withLanguage(event, DEFAULT_LANGUAGE_TAG, {
        userState: user.ok ? UserState.LoggedIn : UserState.LoggedOut,
        user: user.ok ? user.data : null,
        footerText: globals.footerText
    });
};
