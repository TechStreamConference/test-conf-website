import type { RequestEvent } from '@sveltejs/kit';
import { parseSetCookie } from 'set-cookie-parser';

import { client } from '$gen/client.gen';
import { env } from '$env/dynamic/private';

const BACKEND_URL: string | undefined = env['BACKEND_ROOT_URI'];

if (!BACKEND_URL) {
	throw new Error('BACKEND_ROOT_URI is not configured');
}

client.setConfig({
	baseUrl: BACKEND_URL
});

export { client };

/**
 * A `fetch` bound to `event` for calls to the backend. Forwarding the browser's
 * cookies to the backend is already handled by SvelteKit's `event.fetch`; this
 * additionally replays the backend's `Set-Cookie` response headers onto the
 * real response, which does not happen automatically for a cross-service call.
 */
export function backendFetch(event: RequestEvent): typeof fetch {
	return async (input, init) => {
		const response = await event.fetch(input, init);

		for (const { name, value, ...options } of parseSetCookie(response)) {
			// `sameSite` is untyped as a plain `string` by the parser; safe to assert
			// here because the backend is the only source and always sends `lax`.
			event.cookies.set(name, value, {
				path: options.path ?? '/',
				...options,
				sameSite: options.sameSite as 'lax' | 'strict' | 'none' | undefined
			});
		}

		return response;
	};
}
