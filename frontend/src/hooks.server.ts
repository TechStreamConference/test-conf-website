import type { Handle } from '@sveltejs/kit';

// This hook includes the client and forces it to set the base URL.
import '$bff/client';

import { env } from '$env/dynamic/private';

import { DEFAULT_LANGUAGE_TAG } from '$lib/helper/language';

import { applicationStarted } from '$logging/events.gen';
import { applicationStopping } from '$logging/events.gen';
import { httpRequestCompleted } from '$logging/events.gen';
import { httpRequestReceived } from '$logging/events.gen';
import { logger } from '$logging';

const LANG_PLACEHOLDER = '%lang%'; // Has to match the `lang` attribute in `app.html`.

logger.info(
    applicationStarted({
        host: env['HOST'] ?? '0.0.0.0',
        port: parseInt(env['PORT'] ?? '3000', 10)
    })
);

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
    event.locals.languageTag = DEFAULT_LANGUAGE_TAG;
    // The `load` functions run before the page is rendered, so a page can change the language until then.
    const response = await resolve(event, {
        transformPageChunk: ({ html }) => html.replace(LANG_PLACEHOLDER, event.locals.languageTag)
    });
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
