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

import { appendFileSync, mkdirSync } from 'node:fs';
import { dirname } from 'node:path';

import { env } from '$env/dynamic/private';

import type { LogEvent } from './events.gen';

type SeverityText = 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';

type LogRecord = {
	readonly timestamp: string;
	readonly severity_text: SeverityText;
	readonly body: string;
	readonly 'event.name': string;
	readonly attributes: LogEvent['$payload'];
	readonly trace_id: null;
	readonly span_id: null;
};

// ---------------------------------------------------------------------------
// File sink (initialised once at module load)
// ---------------------------------------------------------------------------

const logFilePath: string | undefined = env['LOG_FILE'];

if (logFilePath) {
	mkdirSync(dirname(logFilePath), { recursive: true });
}

// ---------------------------------------------------------------------------
// Internal helpers
// ---------------------------------------------------------------------------

function buildRecord(event: LogEvent, severityText: SeverityText): LogRecord {
	return {
		timestamp: new Date().toISOString(),
		severity_text: severityText,
		body: event.$meta.body,
		'event.name': event.$meta.eventName,
		attributes: event.$payload,
		trace_id: null,
		span_id: null
	};
}

function emit(event: LogEvent, severityText: SeverityText): void {
	const line = JSON.stringify(buildRecord(event, severityText)) + '\n';
	process.stdout.write(line);
	if (logFilePath) {
		appendFileSync(logFilePath, line, 'utf-8');
	}
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

export const logger = {
	debug(event: LogEvent): void {
		emit(event, 'DEBUG');
	},

	info(event: LogEvent): void {
		emit(event, 'INFO');
	},

	warning(event: LogEvent): void {
		emit(event, 'WARNING');
	},

	error(event: LogEvent): void {
		emit(event, 'ERROR');
	},

	critical(event: LogEvent): void {
		emit(event, 'CRITICAL');
	}
};
