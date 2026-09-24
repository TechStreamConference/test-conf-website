/**
 * Structured logging façade for the SvelteKit BFF (server-side only).
 *
 * Usage:
 * ```ts
 * import { logger } from '$logging'
 * import { httpRequestReceived } from '$logging/events.gen'
 *
 * logger.info(httpRequestReceived({ method: 'GET', path: '/v1/globals' }))
 * ```
 *
 * All records are emitted as JSON-lines to `stdout`.  When the `LOG_FILE`
 * environment variable is set, the same records are also appended to that file.
 *
 * The serialized format is intentionally aligned with the OpenTelemetry Logs
 * Data Model so that future trace/span correlation requires no schema changes.
 */

import { appendFileSync } from 'node:fs';
import { dirname } from 'node:path';
import { mkdirSync } from 'node:fs';

import { env } from '$env/dynamic/private';

import type { LogEvent } from './events.gen';

type SeverityText = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

/**
 * @brief Where a log record originates from.
 * `bff` records are produced by the server itself and can be trusted.
 * `browser` records were sent by a client through the log endpoint and have to be treated with suspicion.
 * The value is always set by the server, never by the client.
 */
type LogSource = 'bff' | 'browser';

/**
 * @brief Additional information about the circumstances of a log call, written to the record next to the event.
 */
export interface LogContext {
    /** The path of the page the browser was on. */
    page?: string;
}

/**
 * @brief A log record as it is written to `stdout` and to the log file, aligned with the OpenTelemetry Logs Data Model.
 */
type LogRecord = {
    readonly timestamp: string;
    readonly severity_text: SeverityText;
    readonly body: string;
    readonly 'event.name': string;
    readonly source: LogSource;
    readonly page?: string;
    readonly attributes: LogEvent['$payload'];
    readonly trace_id: null;
    readonly span_id: null;
};

// ---------------------------------------------------------------------------
// File sink (initialised once at module load)
// ---------------------------------------------------------------------------

const LOG_FILE_PATH: string | undefined = env['LOG_FILE'];

if (LOG_FILE_PATH) {
    mkdirSync(dirname(LOG_FILE_PATH), { recursive: true });
}

const IS_DEV: boolean = env['ENVIRONMENT'] === 'dev';

// ---------------------------------------------------------------------------
// Dev pretty-printing (stdout only; never touches the file sink)
// ---------------------------------------------------------------------------

const SERVICE_NAME = 'frontend';

const RESET = '\x1b[0m';
const BOLD = '\x1b[1m';
const DIM = '\x1b[2m';
const RED = '\x1b[31m';
const GREEN = '\x1b[32m';
const YELLOW = '\x1b[33m';
const BLUE = '\x1b[34m';
const MAGENTA = '\x1b[35m';
const CYAN = '\x1b[36m';
const BOLD_RED = '\x1b[1;31m';

const SEVERITY_COLORS: Record<SeverityText, string> = {
    DEBUG: DIM,
    INFO: GREEN,
    WARNING: YELLOW,
    ERROR: RED,
    CRITICAL: BOLD_RED
};

/**
 * @brief Renders a value as indented JSON with ANSI colors for the pretty output during development.
 * @param value the value to render.
 * @param indent the current nesting level.
 * @returns the colored, multi-line string.
 */
function colorizeJson(value: unknown, indent = 0): string {
    const pad = '  '.repeat(indent);
    const inner = '  '.repeat(indent + 1);
    if (value === null) {
        return `${DIM}null${RESET}`;
    }
    if (value === undefined) {
        return `${DIM}undefined${RESET}`;
    }
    if (typeof value === 'boolean') {
        return `${MAGENTA}${value.toString()}${RESET}`;
    }
    if (typeof value === 'number') {
        return `${YELLOW}${value.toString()}${RESET}`;
    }
    if (typeof value === 'string') {
        const escaped = value.replace(/\\/g, '\\\\').replace(/"/g, '\\"');
        return `${GREEN}"${escaped}"${RESET}`;
    }
    if (Array.isArray(value)) {
        if (value.length === 0) return '[]';
        const lines = value.map((v) => `${inner}${colorizeJson(v, indent + 1)}`);
        return `[\n${lines.join(',\n')}\n${pad}]`;
    }
    if (typeof value === 'object') {
        const entries = Object.entries(value as Record<string, unknown>);
        if (entries.length === 0) return '{}';
        const lines = entries.map(
            ([k, v]) => `${inner}${BOLD}${CYAN}"${k}"${RESET}: ${colorizeJson(v, indent + 1)}`
        );
        return `{\n${lines.join(',\n')}\n${pad}}`;
    }
    return JSON.stringify(value);
}

/**
 * @brief Renders a log record for the development console: a colored header line followed by the colored record.
 * @param record the record to render.
 * @returns the multi-line string.
 */
function formatPretty(record: LogRecord): string {
    const severityColor = SEVERITY_COLORS[record.severity_text];
    const header = `${BOLD}${BLUE}[${SERVICE_NAME}]${RESET} ${severityColor}${BOLD}${record.severity_text.padEnd(8)}${RESET} ${BOLD}${record['event.name']}${RESET}`;
    return `${header}\n${colorizeJson(record)}`;
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function buildRecord(
    event: LogEvent,
    severityText: SeverityText,
    source: LogSource,
    context: LogContext | undefined
): LogRecord {
    return {
        timestamp: new Date().toISOString(),
        severity_text: severityText,
        body: event.$meta.body,
        'event.name': event.$meta.eventName,
        source,
        ...(context?.page !== undefined && { page: context.page }),
        attributes: event.$payload,
        trace_id: null,
        span_id: null
    };
}

/**
 * @brief Writes an event to `stdout` and, if `LOG_FILE` is set, to the log file.
 * `stdout` gets the pretty output in development and JSON lines otherwise. The file always gets JSON lines.
 * @param event the event to log.
 * @param severityText the severity of the record.
 * @param source where the event originates from.
 * @param context additional information about the circumstances of the call.
 */
function emit(
    event: LogEvent,
    severityText: SeverityText,
    source: LogSource,
    context: LogContext | undefined
): void {
    const record = buildRecord(event, severityText, source, context);
    const line = JSON.stringify(record) + '\n';
    process.stdout.write(IS_DEV ? formatPretty(record) + '\n' : line);
    if (LOG_FILE_PATH) {
        appendFileSync(LOG_FILE_PATH, line, 'utf-8');
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * @brief Creates a logger whose records are all marked with the given source.
 * @param source the source written to every record.
 * @returns the logger.
 */
function createLogger(source: LogSource) {
    return {
        debug(event: LogEvent, context?: LogContext): void {
            emit(event, 'DEBUG', source, context);
        },

        info(event: LogEvent, context?: LogContext): void {
            emit(event, 'INFO', source, context);
        },

        warning(event: LogEvent, context?: LogContext): void {
            emit(event, 'WARNING', source, context);
        },

        error(event: LogEvent, context?: LogContext): void {
            emit(event, 'ERROR', source, context);
        },

        critical(event: LogEvent, context?: LogContext): void {
            emit(event, 'CRITICAL', source, context);
        }
    };
}

/** The logger for everything the BFF logs itself. */
export const logger = createLogger('bff');

/**
 * @brief The logger for events received from the browser through the log endpoint.
 * Only the log endpoint may use it, because it marks the records as untrusted.
 */
export const browserLogger = createLogger('browser');
