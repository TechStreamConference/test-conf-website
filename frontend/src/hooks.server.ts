// This hook includes the client and forces it to set the base URL.

import '$bff/client';

import type { Handle } from '@sveltejs/kit';

import { env } from '$env/dynamic/private';

import { logger } from '$logging';
import {
	applicationStarted,
	applicationStopping,
	httpRequestCompleted,
	httpRequestReceived
} from '$logging/events.gen';

logger.info(
	applicationStarted({
		host: env['HOST'] ?? '0.0.0.0',
		port: parseInt(env['PORT'] ?? '3000', 10)
	})
);

process.on('SIGTERM', () => {
	logger.info(applicationStopping({}));
});

export const handle: Handle = async ({ event, resolve }) => {
	const start = performance.now();
	logger.info(httpRequestReceived({ method: event.request.method, path: event.url.pathname }));
	const response = await resolve(event);
	logger.info(
		httpRequestCompleted({
			method: event.request.method,
			path: event.url.pathname,
			status_code: response.status,
			duration_ms: Math.round((performance.now() - start) * 100) / 100
		})
	);
	return response;
};
