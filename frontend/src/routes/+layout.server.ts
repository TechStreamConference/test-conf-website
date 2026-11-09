import { getExplicitLanguage } from '$bff/content-language';
import { setLanguageHeaders } from '$bff/content-language';
import { getCurrentUser } from '$bff/v1/auth.server';
import { loadGlobals } from '$bff/v1/globals.server';
import { GenericBackendError } from '$bff/errors';

import { withDefaultLanguage } from '$lib/helper/language';
import { UserState } from '$lib/helper/menus';

import type { LayoutServerLoad } from './$types';

const HTTP_UNAUTHORIZED = 401;

export const load: LayoutServerLoad = async (event) => {
    const [globals, user] = await Promise.all([loadGlobals(event), getCurrentUser(event)]);

    // A 401 only means that nobody is logged in. Every other failure is a real backend error.
    if (!user.ok && user.status !== HTTP_UNAUTHORIZED) {
        throw new GenericBackendError('getCurrentUser', user);
    }

    // The language of the page is the first one that exists of these:
    // the language that a logged-out visitor chose, the language of the user, the default language.
    // A page can replace it with `withLanguage`.
    const explicitLanguage = getExplicitLanguage(event);
    const userLanguageTag = user.ok ? user.data.regionalSettings?.locale : undefined;
    setLanguageHeaders(event, user.ok || explicitLanguage !== undefined);
    return withDefaultLanguage(event, explicitLanguage ?? userLanguageTag, {
        userState: user.ok ? UserState.LoggedIn : UserState.LoggedOut,
        user: user.ok ? user.data : null,
        footerText: globals.footerText
    });
};
