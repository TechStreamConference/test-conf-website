import type { RequestHandler } from '@sveltejs/kit';
import { z } from 'zod';

import { env } from '$env/dynamic/private';

import { MAX_PAGE_LENGTH } from '$logging/client';
import { BROWSER_EVENT_PARSERS } from '$logging/events.gen';
import { RateLimiter } from '$logging/rate-limit';
import { browserLogger } from '$logging';

/**
 * @brief Reads a positive integer from the environment.
 * @param name the name of the environment variable.
 * @returns the value.
 * @throws Error if the variable is missing or not a positive integer.
 */
function readPositiveInt(name: string): number {
    const value = Number(env[name]);
    if (!Number.isInteger(value) || value <= 0) {
        throw new Error(`${name} is not configured as a positive integer`);
    }
    return value;
}

/**
 * @brief The limits of the endpoint, read from the environment.
 */
interface Limits {
    rateLimiter: RateLimiter;
    maxBodyBytes: number;
}

let limits: Limits | undefined;

/**
 * @brief Returns the limits of the endpoint, created on first use.
 * The rate limiter is global: all clients share it, so the log file cannot be flooded no matter how many
 * addresses the requests come from.
 * The limits are not read at module load, because SvelteKit loads the routes during the build, when the environment is not set.
 * @returns the limits.
 * @throws Error if `LOG_BROWSER_RATE_LIMIT_BURST`, `LOG_BROWSER_RATE_LIMIT_PER_MINUTE` or `LOG_BROWSER_MAX_BODY_BYTES` is not configured.
 */
function getLimits(): Limits {
    limits ??= {
        rateLimiter: new RateLimiter(
            readPositiveInt('LOG_BROWSER_RATE_LIMIT_BURST'),
            readPositiveInt('LOG_BROWSER_RATE_LIMIT_PER_MINUTE') / 60
        ),
        maxBodyBytes: readPositiveInt('LOG_BROWSER_MAX_BODY_BYTES')
    };
    return limits;
}

const EnvelopeSchema = z.object({
    event: z.string(),
    severity: z.enum(['warning', 'error']),
    payload: z.unknown(),
    page: z.string().max(MAX_PAGE_LENGTH).optional()
});

/**
 * @brief Receives a log event from the browser and writes it with the source `browser`.
 * Only known events with a valid payload are accepted and only the severities `warning` and `error`.
 * The endpoint is rate limited globally.
 * @throws Error if the limits are not configured.
 * @param request the incoming request.
 * @returns `204` on success, otherwise an error status without body.
 */
export const POST: RequestHandler = async ({ request }) => {
    const { rateLimiter, maxBodyBytes } = getLimits();

    const rateLimit = rateLimiter.consume();
    if (!rateLimit.allowed) {
        return new Response(null, {
            status: 429,
            headers: { 'Retry-After': rateLimit.retryAfterSeconds.toString() }
        });
    }

    // A cross-origin request with this content type needs a CORS preflight, which is never answered.
    if (!request.headers.get('content-type')?.startsWith('application/json')) {
        return new Response(null, { status: 415 });
    }

    const declaredLength = Number(request.headers.get('content-length') ?? 0);
    if (declaredLength > maxBodyBytes) {
        return new Response(null, { status: 413 });
    }
    const text = await request.text();
    if (new TextEncoder().encode(text).length > maxBodyBytes) {
        return new Response(null, { status: 413 });
    }

    let json: unknown;
    try {
        json = JSON.parse(text);
    } catch {
        return new Response(null, { status: 400 });
    }

    const envelope = EnvelopeSchema.safeParse(json);
    if (!envelope.success) {
        return new Response(null, { status: 400 });
    }

    const { event: eventName, severity, payload, page } = envelope.data;
    const parser = Object.hasOwn(BROWSER_EVENT_PARSERS, eventName)
        ? BROWSER_EVENT_PARSERS[eventName]
        : undefined;
    const event = parser?.(payload);
    if (event === undefined) {
        return new Response(null, { status: 400 });
    }

    browserLogger[severity](event, page === undefined ? undefined : { page });
    return new Response(null, { status: 204 });
};
