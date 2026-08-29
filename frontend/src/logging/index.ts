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

const isDev: boolean = env['ENVIRONMENT'] === 'dev';

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

function formatPretty(record: LogRecord): string {
	const severityColor = SEVERITY_COLORS[record.severity_text];
	const header = `${BOLD}${BLUE}[${SERVICE_NAME}]${RESET} ${severityColor}${BOLD}${record.severity_text.padEnd(8)}${RESET} ${BOLD}${record['event.name']}${RESET}`;
	return `${header}\n${colorizeJson(record)}`;
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
	const record = buildRecord(event, severityText);
	const line = JSON.stringify(record) + '\n';
	process.stdout.write(isDev ? formatPretty(record) + '\n' : line);
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
