import type { RequestEvent } from '@sveltejs/kit';

import { loginCallbackV1 } from '$gen/sdk.gen';
import type { LoginCallbackResponseV1, LoginCallbackV1Error } from '$gen/types.gen';

import { logger } from '$logging';
import { backendCallCompleted } from '$logging/events.gen';

export type LoginCallbackResult =
	{ ok: true; data: LoginCallbackResponseV1 } | { ok: false; error: LoginCallbackV1Error };

export async function forwardLoginCallback(event: RequestEvent): Promise<LoginCallbackResult> {
	const start = performance.now();
	const { data, error, response } = await loginCallbackV1({
		fetch: event.fetch,
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
