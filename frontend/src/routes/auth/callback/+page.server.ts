//
// Tech Stream Conference
// 2026
//
// Handles the identity provider callback on the server.
//

import { redirect } from '@sveltejs/kit';

import { forwardLoginCallback } from '$bff/v1/auth.server';

import type { LoginCallbackV1Error } from '$gen/types.gen';

import type { PageServerLoad } from './$types';

export type LoginCallbackPageData = { error: LoginCallbackV1Error };

export const load: PageServerLoad = async (event) => {
    const result = await forwardLoginCallback(event);

    if (result.ok) {
        redirect(302, result.data.redirect_url);
    }

    return { error: result.error } satisfies LoginCallbackPageData;
};
