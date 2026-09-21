//
// Tech Stream Conference
// 2026
//
// Forwards the login callback to the backend.
//

import type { RequestEvent } from '@sveltejs/kit';

import { backendFetch } from '$bff/client';

import type { LoginCallbackResponseV1 } from '$gen/types.gen';
import type { LoginCallbackV1Error } from '$gen/types.gen';
import { loginCallbackV1 } from '$gen/sdk.gen';

import { backendCallCompleted } from '$logging/events.gen';
import { logger } from '$logging';

export type LoginCallbackResult =
    { ok: true; data: LoginCallbackResponseV1 } | { ok: false; error: LoginCallbackV1Error };

/**
 * @brief Forwards the identity provider callback (`state`, `code` and `error` query parameters) to the backend.
 * @param event the request event of the callback.
 * @returns the backend response on success, the backend error otherwise.
 */
export async function forwardLoginCallback(event: RequestEvent): Promise<LoginCallbackResult> {
    const start = performance.now();
    const { data, error, response } = await loginCallbackV1({
        fetch: backendFetch(event),
        query: {
            state: event.url.searchParams.get('state'),
            code: event.url.searchParams.get('code'),
            error: event.url.searchParams.get('error')
        }
    });
    logger.info(
        backendCallCompleted({
            operation_id: 'loginCallbackV1',
            status_code: response?.status ?? 0,
            duration_ms: Math.round((performance.now() - start) * 100) / 100
        })
    );

    if (error) {
        return { ok: false, error };
    }

    // `error` being falsy (an object type, hence always truthy when present) proves
    // `data` is defined, unlike `GenericBackendError`’s call sites with `unknown` errors.
    return { ok: true, data };
}
