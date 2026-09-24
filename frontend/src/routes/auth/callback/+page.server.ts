import { redirect } from '@sveltejs/kit';

import { forwardLoginCallback } from '$bff/v1/auth.server';

import type { LoginCallbackV1Error } from '$gen/types.gen';

import type { PageServerLoad } from './$types';

/**
 * @brief The page data of the callback page. It is only rendered if the login failed.
 */
export type LoginCallbackPageData = { error: LoginCallbackV1Error };

/**
 * @brief Forwards the identity provider callback to the backend. Redirects on success.
 * @param event the request event of the callback.
 * @returns the error to render if the login failed.
 */
export const load: PageServerLoad = async (event) => {
    const result = await forwardLoginCallback(event);

    if (result.ok) {
        redirect(302, result.data.redirect_url);
    }

    return { error: result.error } satisfies LoginCallbackPageData;
};
