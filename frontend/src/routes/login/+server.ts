import { error, redirect } from '@sveltejs/kit';

import type { RequestHandler } from './$types';

// A raw redirect rather than a forwarded fetch: the backend itself owns the
// redirect target (ZITADEL) and any validation error for `redirect_url`.
export const GET: RequestHandler = ({ url }) => {
	const redirectUrl = url.searchParams.get('redirect_url');
	if (!redirectUrl) {
		error(400, 'Missing required "redirect_url" query parameter.');
	}

	const params = new URLSearchParams({ redirect_url: redirectUrl });

	redirect(302, `/api/v1/auth/login?${params}`);
};
