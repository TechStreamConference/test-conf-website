//
// Tech Stream Conference
// 2026
//
// Redirects the login request to the backend.
//

import { error } from '@sveltejs/kit';
import { redirect } from '@sveltejs/kit';

import type { RequestHandler } from './$types';

/**
 * @brief Redirects the login request to the backend.
 * This is a raw redirect rather than a forwarded fetch: the backend itself owns the
 * redirect target (ZITADEL) and any validation error for `redirect_url`.
 * @param url the request URL. It must contain the `redirect_url` query parameter.
 * @throws HttpError with status 400 if `redirect_url` is missing.
 * @throws Redirect to the login endpoint of the backend.
 */
export const GET: RequestHandler = ({ url }) => {
    const redirectUrl = url.searchParams.get('redirect_url');
    if (!redirectUrl) {
        error(400, 'Missing required "redirect_url" query parameter.');
    }

    const params = new URLSearchParams({ redirect_url: redirectUrl });

    redirect(302, `/api/v1/auth/login?${params}`);
};
