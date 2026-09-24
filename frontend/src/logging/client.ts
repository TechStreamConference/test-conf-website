import { browser } from '$app/environment';

import type { BrowserLogEvent } from './events.gen';

/**
 * @brief The severities a client is allowed to log with.
 */
export type ClientSeverity = 'warning' | 'error';

/**
 * @brief Writes an event on the server. Registered by the server hooks, see `registerServerSink`.
 */
type ServerSink = (event: BrowserLogEvent, severity: ClientSeverity) => void;

/** The longest page path that is sent. Longer paths are cut off. */
export const MAX_PAGE_LENGTH = 200;

/** The path of the endpoint the browser sends its events to. */
export const LOG_ENDPOINT = '/bff/log';

let serverSink: ServerSink | undefined;

/**
 * @brief Registers the function that writes events when the code runs on the server.
 * The sink is registered instead of imported so that this module stays free of server-only code
 * and can be imported from code that runs in the browser as well.
 * @param sink the function writing the event with the server logger.
 */
export function registerServerSink(sink: ServerSink): void {
    serverSink = sink;
}

/**
 * @brief Logs an event no matter whether the code runs in the browser or on the server.
 * In the browser the event is sent to the log endpoint together with the path of the current page,
 * on the server it is written directly.
 * Failures are ignored, because logging must never break the page.
 * @param event the event to log.
 * @param severity the severity of the record.
 */
function log(event: BrowserLogEvent, severity: ClientSeverity): void {
    if (browser) {
        try {
            fetch(LOG_ENDPOINT, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    event: event.$meta.eventName,
                    severity,
                    payload: event.$payload,
                    page: window.location.pathname.slice(0, MAX_PAGE_LENGTH)
                }),
                keepalive: true
            }).catch(() => undefined);
        } catch {
            // Logging must never break the page.
        }
        return;
    }
    // Without a registered sink (e.g. in unit tests) the event is dropped.
    serverSink?.(event, severity);
}

/** Logger for code that runs in the browser and on the server. */
export const clientLogger = {
    warning(event: BrowserLogEvent): void {
        log(event, 'warning');
    },

    error(event: BrowserLogEvent): void {
        log(event, 'error');
    }
};
