//
// Tech Stream Conference
// 2026
//
// Configures the backend client and forwards backend cookies.
//

import type { RequestEvent } from '@sveltejs/kit';
import { parseSetCookie } from 'set-cookie-parser';

import { env } from '$env/dynamic/private';

import { client } from '$gen/client.gen';

export { client };

/**
 * @brief Sets the base URL of the generated backend client from `BACKEND_ROOT_URI`.
 * @throws Error if `BACKEND_ROOT_URI` is not configured.
 */
function configureClient(): void {
    const backendUrl: string | undefined = env['BACKEND_ROOT_URI'];

    if (!backendUrl) {
        throw new Error('BACKEND_ROOT_URI is not configured');
    }

    client.setConfig({
        baseUrl: backendUrl
    });
}

/**
 * @brief A `fetch` bound to `event` for calls to the backend. Forwarding the browser's
 * cookies to the backend is already handled by SvelteKit's `event.fetch`; this
 * additionally replays the backend's `Set-Cookie` response headers onto the
 * real response, which does not happen automatically for a cross-service call.
 * @param event the request event whose `fetch` and cookies are used
 * @returns a `fetch` that forwards the backend's `Set-Cookie` headers to the response
 */
export function backendFetch(event: RequestEvent): typeof fetch {
    configureClient();

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
