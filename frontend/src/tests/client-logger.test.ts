import { afterEach } from 'vitest';
import { beforeEach } from 'vitest';
import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

const state = vi.hoisted(() => ({ browser: false }));

vi.mock('$app/environment', () => ({
    get browser(): boolean {
        return state.browser;
    }
}));

import type * as ClientModule from '$logging/client';
import { validatorNotUnsignedInt } from '$logging/events.gen';

const EVENT = validatorNotUnsignedInt({ origin: 'test.origin', value: '-3' });

/**
 * @brief Loads the module anew, because it keeps the registered sink in module state.
 * @returns the module.
 */
async function loadClient(): Promise<typeof ClientModule> {
    vi.resetModules();
    return await import('$logging/client');
}

/**
 * @brief Pretends to run in a browser on the given page.
 * @param pathname the path of the current page.
 * @returns the replacement for `fetch`.
 */
function pretendBrowser(pathname: string) {
    state.browser = true;
    vi.stubGlobal('window', { location: { pathname } });
    const fetchMock = vi.fn(() => Promise.resolve(new Response(null, { status: 204 })));
    vi.stubGlobal('fetch', fetchMock);
    return fetchMock;
}

/**
 * @brief Reads the JSON body of the first request that was sent.
 * @param fetchMock the replacement for `fetch`.
 * @returns the parsed body.
 * @throws Error if the body was not sent as a string.
 */
function sentBody(fetchMock: ReturnType<typeof pretendBrowser>): unknown {
    const [, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
    if (typeof init.body !== 'string') {
        throw new Error('The body was not sent as a string');
    }
    return JSON.parse(init.body);
}

beforeEach(() => {
    state.browser = false;
});

afterEach(() => {
    vi.unstubAllGlobals();
    vi.clearAllMocks();
});

describe('clientLogger in the browser', () => {
    it('should send the event to the log endpoint', async () => {
        const fetchMock = pretendBrowser('/login');
        const { clientLogger } = await loadClient();
        clientLogger.warning(EVENT);
        expect(fetchMock).toHaveBeenCalledOnce();
        const [url, init] = fetchMock.mock.calls[0] as unknown as [string, RequestInit];
        expect(url).toBe('/bff/log');
        expect(init.method).toBe('POST');
        expect(init.headers).toEqual({ 'Content-Type': 'application/json' });
        expect(init.keepalive).toBe(true);
    });

    it('should send the event name, severity, payload and page', async () => {
        const fetchMock = pretendBrowser('/login');
        const { clientLogger } = await loadClient();
        clientLogger.warning(EVENT);
        expect(sentBody(fetchMock)).toEqual({
            event: 'validator.not_unsigned_int',
            severity: 'warning',
            payload: EVENT.$payload,
            page: '/login'
        });
    });

    it('should send the severity error', async () => {
        const fetchMock = pretendBrowser('/');
        const { clientLogger } = await loadClient();
        clientLogger.error(EVENT);
        expect(sentBody(fetchMock)).toMatchObject({ severity: 'error' });
    });

    it('should cut off a page that is too long', async () => {
        const fetchMock = pretendBrowser('/' + 'a'.repeat(500));
        const { clientLogger, MAX_PAGE_LENGTH } = await loadClient();
        clientLogger.warning(EVENT);
        const body = sentBody(fetchMock) as { page: string };
        expect(body.page).toHaveLength(MAX_PAGE_LENGTH);
    });

    it('should not call the sink of the server', async () => {
        pretendBrowser('/');
        const { clientLogger, registerServerSink } = await loadClient();
        const sink = vi.fn();
        registerServerSink(sink);
        clientLogger.warning(EVENT);
        expect(sink).not.toHaveBeenCalled();
    });

    it('should not throw when the request fails', async () => {
        pretendBrowser('/');
        vi.stubGlobal(
            'fetch',
            vi.fn(() => Promise.reject(new Error('offline')))
        );
        const { clientLogger } = await loadClient();
        expect(() => {
            clientLogger.warning(EVENT);
        }).not.toThrow();
        // Give a rejected promise the chance to surface as an unhandled rejection.
        await new Promise((resolve) => setTimeout(resolve, 0));
    });

    it('should not throw when fetch itself throws', async () => {
        pretendBrowser('/');
        vi.stubGlobal(
            'fetch',
            vi.fn(() => {
                throw new Error('broken');
            })
        );
        const { clientLogger } = await loadClient();
        expect(() => {
            clientLogger.warning(EVENT);
        }).not.toThrow();
    });
});

describe('clientLogger on the server', () => {
    it('should call the registered sink with the event and severity', async () => {
        const { clientLogger, registerServerSink } = await loadClient();
        const sink = vi.fn();
        registerServerSink(sink);
        clientLogger.warning(EVENT);
        clientLogger.error(EVENT);
        expect(sink).toHaveBeenCalledTimes(2);
        expect(sink).toHaveBeenNthCalledWith(1, EVENT, 'warning');
        expect(sink).toHaveBeenNthCalledWith(2, EVENT, 'error');
    });

    it('should not send a request', async () => {
        const fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        const { clientLogger, registerServerSink } = await loadClient();
        registerServerSink(vi.fn());
        clientLogger.warning(EVENT);
        expect(fetchMock).not.toHaveBeenCalled();
    });

    it('should use the sink that was registered last', async () => {
        const { clientLogger, registerServerSink } = await loadClient();
        const first = vi.fn();
        const second = vi.fn();
        registerServerSink(first);
        registerServerSink(second);
        clientLogger.warning(EVENT);
        expect(first).not.toHaveBeenCalled();
        expect(second).toHaveBeenCalledOnce();
    });

    it('should drop the event without a registered sink', async () => {
        const fetchMock = vi.fn();
        vi.stubGlobal('fetch', fetchMock);
        const { clientLogger } = await loadClient();
        expect(() => {
            clientLogger.warning(EVENT);
        }).not.toThrow();
        expect(fetchMock).not.toHaveBeenCalled();
    });
});
