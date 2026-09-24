import type { Handle } from '@sveltejs/kit';

// This hook includes the client and forces it to set the base URL.
import '$bff/client';

import { env } from '$env/dynamic/private';

import { applicationStarted } from '$logging/events.gen';
import { applicationStopping } from '$logging/events.gen';
import { httpRequestCompleted } from '$logging/events.gen';
import { httpRequestReceived } from '$logging/events.gen';
import { registerServerSink } from '$logging/client';
import { logger } from '$logging';

logger.info(
    applicationStarted({
        host: env['HOST'] ?? '0.0.0.0',
        port: parseInt(env['PORT'] ?? '3000', 10)
    })
);

// Lets code that also runs in the browser log through the server logger when it runs on the server.
registerServerSink((event, severity) => {
    logger[severity](event);
});

process.on('SIGTERM', () => {
    logger.info(applicationStopping({}));
});

/**
 * @brief Logs every request when it is received and when it is completed, including status code and duration.
 * @param event the current request event.
 * @param resolve renders the response for the event.
 * @returns the resolved response.
 */
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
