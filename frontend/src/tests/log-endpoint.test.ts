import type { RequestHandler } from '@sveltejs/kit';
import { afterEach } from 'vitest';
import { beforeEach } from 'vitest';
import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

const mocks = vi.hoisted(() => {
    const env: Record<string, string | undefined> = {};
    return {
        env,
        logger: { warning: vi.fn(), error: vi.fn() },
        browserLogger: { warning: vi.fn(), error: vi.fn() }
    };
});

vi.mock('$env/dynamic/private', () => ({ env: mocks.env }));
vi.mock('$logging', () => ({ logger: mocks.logger, browserLogger: mocks.browserLogger }));

import { MAX_PAGE_LENGTH } from '$logging/client';
import { imageBothDimensionsSet } from '$logging/events.gen';
import { validatorNotUnsignedInt } from '$logging/events.gen';

type PostHandler = RequestHandler;

const VALID_BODY = {
    event: 'validator.not_unsigned_int',
    severity: 'warning',
    payload: { origin: 'test.origin', value: '-3' }
};

const VALID_EVENT = validatorNotUnsignedInt({
    origin: 'test.origin',
    value: '-3'
});

/**
 * @brief Loads the endpoint new, because it keeps its limits in module state.
 * @returns the handler of the endpoint.
 */
async function loadPost(): Promise<PostHandler> {
    vi.resetModules();
    return (await import('../routes/bff/log/+server')).POST;
}

/**
 * @brief Calls the handler with a request.
 * @param post the handler.
 * @param request the request to send.
 * @returns the response.
 */
async function send(post: PostHandler, request: Request | object): Promise<Response> {
    return await post({ request } as Parameters<PostHandler>[0]);
}

/**
 * @brief Builds a request for the endpoint.
 * @param body the JSON body, or a string that is sent as it is.
 * @param contentType the content type header, `null` to omit it.
 * @returns the request.
 */
function makeRequest(body: unknown, contentType: string | null = 'application/json'): Request {
    const headers = new Headers();
    if (contentType !== null) {
        headers.set('content-type', contentType);
    }
    return new Request('http://localhost/bff/log', {
        method: 'POST',
        headers,
        body: typeof body === 'string' ? body : JSON.stringify(body)
    });
}

beforeEach(() => {
    mocks.env['LOG_BROWSER_RATE_LIMIT_BURST'] = '3';
    mocks.env['LOG_BROWSER_RATE_LIMIT_PER_MINUTE'] = '30';
    mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = '200';
    vi.useFakeTimers({ toFake: ['Date'] });
    vi.setSystemTime(1_000_000);
});

afterEach(() => {
    vi.useRealTimers();
    vi.clearAllMocks();
});

describe('log endpoint: accepted events', () => {
    it('should log a valid event with the severity warning and answer 204', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest(VALID_BODY));
        expect(response.status).toBe(204);
        expect(mocks.browserLogger.warning).toHaveBeenCalledOnce();
        expect(mocks.browserLogger.warning).toHaveBeenCalledWith(VALID_EVENT, undefined);
        expect(mocks.browserLogger.error).not.toHaveBeenCalled();
    });

    it('should log a valid event with the severity error', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest({ ...VALID_BODY, severity: 'error' }));
        expect(response.status).toBe(204);
        expect(mocks.browserLogger.error).toHaveBeenCalledOnce();
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it('should never use the logger of the bff for events from the browser', async () => {
        const post = await loadPost();
        await send(post, makeRequest(VALID_BODY));
        await send(post, makeRequest({ ...VALID_BODY, severity: 'error' }));
        expect(mocks.logger.warning).not.toHaveBeenCalled();
        expect(mocks.logger.error).not.toHaveBeenCalled();
    });

    it('should accept an event with an optional field', async () => {
        const post = await loadPost();
        const payload = { url: '/logo.png', height: '10rem', width: '20rem' };
        const response = await send(
            post,
            makeRequest({ event: 'image.both_dimensions_set', severity: 'warning', payload })
        );
        expect(response.status).toBe(204);
        expect(mocks.browserLogger.warning).toHaveBeenCalledWith(
            imageBothDimensionsSet(payload),
            undefined
        );
    });

    it('should drop unknown fields from the payload', async () => {
        const post = await loadPost();
        const response = await send(
            post,
            makeRequest({
                ...VALID_BODY,
                source: 'bff',
                payload: { ...VALID_BODY.payload, source: 'bff', extra: 'x' }
            })
        );
        expect(response.status).toBe(204);
        expect(mocks.browserLogger.warning).toHaveBeenCalledWith(VALID_EVENT, undefined);
    });
});

describe('log endpoint: page', () => {
    it('should pass the page to the logger', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest({ ...VALID_BODY, page: '/login' }));
        expect(response.status).toBe(204);
        expect(mocks.browserLogger.warning).toHaveBeenCalledWith(VALID_EVENT, { page: '/login' });
    });

    it('should accept a page of exactly the maximum length', async () => {
        mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = '2048';
        const post = await loadPost();
        const page = '/'.repeat(MAX_PAGE_LENGTH);
        expect((await send(post, makeRequest({ ...VALID_BODY, page }))).status).toBe(204);
    });

    it('should answer 400 for a page that is too long', async () => {
        mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = '2048';
        const post = await loadPost();
        const page = '/'.repeat(MAX_PAGE_LENGTH + 1);
        expect((await send(post, makeRequest({ ...VALID_BODY, page }))).status).toBe(400);
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it.each([42, null, ['/login'], { path: '/login' }])(
        'should answer 400 when the page is not a string: %j',
        async (page) => {
            const post = await loadPost();
            expect((await send(post, makeRequest({ ...VALID_BODY, page }))).status).toBe(400);
        }
    );

    it('should not let the payload set the page', async () => {
        const post = await loadPost();
        await send(
            post,
            makeRequest({ ...VALID_BODY, payload: { ...VALID_BODY.payload, page: '/evil' } })
        );
        expect(mocks.browserLogger.warning).toHaveBeenCalledWith(VALID_EVENT, undefined);
    });
});

describe('log endpoint: rejected requests', () => {
    it('should answer 415 for another content type', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest(VALID_BODY, 'text/plain'));
        expect(response.status).toBe(415);
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it('should answer 415 for a missing content type', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest(VALID_BODY, null));
        expect(response.status).toBe(415);
    });

    it('should answer 413 when the declared length is too large', async () => {
        const post = await loadPost();
        const request = {
            headers: new Headers({ 'content-type': 'application/json', 'content-length': '5000' }),
            text: () => Promise.resolve(JSON.stringify(VALID_BODY))
        };
        const response = await send(post, request);
        expect(response.status).toBe(413);
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it('should answer 413 when the body is larger than the declared length', async () => {
        const post = await loadPost();
        const request = {
            headers: new Headers({ 'content-type': 'application/json', 'content-length': '10' }),
            text: () => Promise.resolve('x'.repeat(201))
        };
        const response = await send(post, request);
        expect(response.status).toBe(413);
    });

    it('should count the size of the body in bytes and not in characters', async () => {
        const post = await loadPost();
        // 100 characters with two bytes each are 200 bytes plus the JSON around them.
        const body = {
            event: 'image.both_dimensions_set',
            severity: 'warning',
            payload: { url: 'ä'.repeat(100), height: '1', width: '1' }
        };
        const response = await send(post, makeRequest(body));
        expect(response.status).toBe(413);
    });

    it('should accept a body of exactly the maximum size', async () => {
        const body = JSON.stringify(VALID_BODY);
        mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = body.length.toString();
        const post = await loadPost();
        expect((await send(post, makeRequest(body))).status).toBe(204);
    });

    it('should reject a body one byte over the maximum size', async () => {
        const body = JSON.stringify(VALID_BODY);
        mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = (body.length - 1).toString();
        const post = await loadPost();
        expect((await send(post, makeRequest(body))).status).toBe(413);
    });

    it('should answer 400 for invalid JSON', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest('{not json'));
        expect(response.status).toBe(400);
    });

    it('should answer 400 when the event is missing', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest({ severity: 'warning', payload: {} }));
        expect(response.status).toBe(400);
    });

    it('should answer 400 when the severity is missing', async () => {
        const post = await loadPost();
        const response = await send(
            post,
            makeRequest({ event: VALID_BODY.event, payload: VALID_BODY.payload })
        );
        expect(response.status).toBe(400);
    });

    it.each(['critical', 'info', 'debug', 'WARNING', ''])(
        'should answer 400 for the severity "%s"',
        async (severity) => {
            const post = await loadPost();
            const response = await send(post, makeRequest({ ...VALID_BODY, severity }));
            expect(response.status).toBe(400);
            expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
            expect(mocks.browserLogger.error).not.toHaveBeenCalled();
        }
    );

    it.each(['http.request.received', 'application.started', 'does.not.exist', ''])(
        'should answer 400 for the event that is not allowed for the browser "%s"',
        async (event) => {
            const post = await loadPost();
            const response = await send(
                post,
                makeRequest({ event, severity: 'warning', payload: {} })
            );
            expect(response.status).toBe(400);
            expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
        }
    );

    it.each(['constructor', '__proto__', 'toString', 'hasOwnProperty'])(
        'should answer 400 for the event name "%s" from the object prototype',
        async (event) => {
            const post = await loadPost();
            const response = await send(
                post,
                makeRequest({ event, severity: 'warning', payload: {} })
            );
            expect(response.status).toBe(400);
        }
    );

    it('should answer 400 when the payload does not match the schema', async () => {
        const post = await loadPost();
        const response = await send(
            post,
            makeRequest({ ...VALID_BODY, payload: { ...VALID_BODY.payload, value: 3 } })
        );
        expect(response.status).toBe(400);
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it('should answer 400 when a required field of the payload is missing', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest({ ...VALID_BODY, payload: {} }));
        expect(response.status).toBe(400);
    });

    it('should answer 400 when the payload is missing', async () => {
        const post = await loadPost();
        const response = await send(
            post,
            makeRequest({ event: VALID_BODY.event, severity: 'warning' })
        );
        expect(response.status).toBe(400);
    });

    it.each(['null', '[]', '"text"', '42'])(
        'should answer 400 when the body is the JSON value %s',
        async (body) => {
            const post = await loadPost();
            expect((await send(post, makeRequest(body))).status).toBe(400);
        }
    );

    it('should not answer with a body for an error', async () => {
        const post = await loadPost();
        const response = await send(post, makeRequest('{not json'));
        expect(await response.text()).toBe('');
    });
});

describe('log endpoint: rate limit', () => {
    it('should allow the burst and then answer 429', async () => {
        const post = await loadPost();
        for (let i = 0; i < 3; i++) {
            expect((await send(post, makeRequest(VALID_BODY))).status).toBe(204);
        }
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(429);
        expect(mocks.browserLogger.warning).toHaveBeenCalledTimes(3);
    });

    it('should tell how long to wait in the Retry-After header', async () => {
        const post = await loadPost();
        for (let i = 0; i < 3; i++) {
            await send(post, makeRequest(VALID_BODY));
        }
        const response = await send(post, makeRequest(VALID_BODY));
        // 30 per minute are 0.5 per second, so the next token takes two seconds.
        expect(response.headers.get('retry-after')).toBe('2');
    });

    it('should allow requests again after the time has passed', async () => {
        const post = await loadPost();
        for (let i = 0; i < 3; i++) {
            await send(post, makeRequest(VALID_BODY));
        }
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(429);
        vi.setSystemTime(1_000_000 + 2000);
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(204);
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(429);
    });

    it('should count invalid requests too', async () => {
        const post = await loadPost();
        for (let i = 0; i < 3; i++) {
            expect((await send(post, makeRequest('{not json'))).status).toBe(400);
        }
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(429);
    });

    it('should check the rate limit before the content type', async () => {
        const post = await loadPost();
        for (let i = 0; i < 3; i++) {
            await send(post, makeRequest(VALID_BODY));
        }
        expect((await send(post, makeRequest(VALID_BODY, 'text/plain'))).status).toBe(429);
    });

    it('should share the limit between all requests', async () => {
        const post = await loadPost();
        // The handler gets no address, so nothing about the client can matter.
        await send(post, makeRequest(VALID_BODY));
        await send(post, makeRequest(VALID_BODY));
        await send(post, makeRequest(VALID_BODY));
        const other = new Request('http://other.example/bff/log', {
            method: 'POST',
            headers: { 'content-type': 'application/json', 'x-forwarded-for': '203.0.113.9' },
            body: JSON.stringify(VALID_BODY)
        });
        expect((await send(post, other)).status).toBe(429);
    });

    it('should use the burst from the environment', async () => {
        mocks.env['LOG_BROWSER_RATE_LIMIT_BURST'] = '1';
        const post = await loadPost();
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(204);
        expect((await send(post, makeRequest(VALID_BODY))).status).toBe(429);
    });

    it('should use the rate per minute from the environment', async () => {
        mocks.env['LOG_BROWSER_RATE_LIMIT_BURST'] = '1';
        mocks.env['LOG_BROWSER_RATE_LIMIT_PER_MINUTE'] = '60';
        const post = await loadPost();
        await send(post, makeRequest(VALID_BODY));
        const response = await send(post, makeRequest(VALID_BODY));
        // 60 per minute is one per second.
        expect(response.headers.get('retry-after')).toBe('1');
    });
});

describe('log endpoint: configuration', () => {
    it.each([
        'LOG_BROWSER_RATE_LIMIT_BURST',
        'LOG_BROWSER_RATE_LIMIT_PER_MINUTE',
        'LOG_BROWSER_MAX_BODY_BYTES'
    ])('should throw when %s is missing', async (name) => {
        mocks.env[name] = undefined;
        const post = await loadPost();
        await expect(send(post, makeRequest(VALID_BODY))).rejects.toThrow(name);
    });

    it.each(['', 'abc', '0', '-1', '1.5', '2048;', ' ', 'NaN', 'Infinity'])(
        'should throw when a limit is the invalid value "%s"',
        async (value) => {
            mocks.env['LOG_BROWSER_MAX_BODY_BYTES'] = value;
            const post = await loadPost();
            await expect(send(post, makeRequest(VALID_BODY))).rejects.toThrow(
                'LOG_BROWSER_MAX_BODY_BYTES'
            );
        }
    );

    it('should not log anything when the configuration is invalid', async () => {
        delete mocks.env['LOG_BROWSER_RATE_LIMIT_BURST'];
        const post = await loadPost();
        await expect(send(post, makeRequest(VALID_BODY))).rejects.toThrow();
        expect(mocks.browserLogger.warning).not.toHaveBeenCalled();
    });

    it('should not read the environment when the module is loaded', async () => {
        delete mocks.env['LOG_BROWSER_RATE_LIMIT_BURST'];
        delete mocks.env['LOG_BROWSER_RATE_LIMIT_PER_MINUTE'];
        delete mocks.env['LOG_BROWSER_MAX_BODY_BYTES'];
        await expect(loadPost()).resolves.toBeTypeOf('function');
    });
});
