//
// Tech Stream Conference
// 2026
//
// Loads the global data from the backend.
//

import type { RequestEvent } from '@sveltejs/kit';

import { backendFetch } from '$bff/client';
import { GenericBackendError } from '$bff/errors';
import { UndefinedDataError } from '$bff/errors';

import type { GlobalsResponseV1 } from '$gen/types.gen';
import { getGlobalsV1 } from '$gen/sdk.gen';

import { backendCallCompleted } from '$logging/events.gen';
import { logger } from '$logging';

/**
 * @brief Loads the global data from the backend.
 * @param event the request event used for the backend call.
 * @returns the global data.
 * @throws GenericBackendError if the backend returns an error.
 * @throws UndefinedDataError if the backend returns no data.
 */
export async function loadGlobals(event: RequestEvent): Promise<GlobalsResponseV1> {
    const start = performance.now();
    const { data, error, response } = await getGlobalsV1({ fetch: backendFetch(event) });
    logger.info(
        backendCallCompleted({
            operation_id: 'getGlobalsV1',
            status_code: response?.status ?? 0,
            duration_ms: Math.round((performance.now() - start) * 100) / 100
        })
    );

    if (error) {
        throw new GenericBackendError('loadGlobals', error);
    }

    if (data == undefined) {
        throw new UndefinedDataError('loadGlobals');
    }

    return data;
}
