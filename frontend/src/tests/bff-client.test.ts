import type { RequestEvent } from '@sveltejs/kit';
import type { Mock } from 'vitest';
import { beforeEach } from 'vitest';
import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

import { backendFetch } from '$bff/client';

vi.mock('$env/dynamic/private', () => ({
    env: { BACKEND_ROOT_URI: 'http://backend.test' }
}));

vi.mock('$gen/client.gen', () => ({
    client: { setConfig: vi.fn() }
}));

const BACKEND_URL = 'http://backend.test/v1/something';

interface FakeEvent {
    event: RequestEvent;
    fetchMock: Mock<typeof fetch>;
    setCookieMock: Mock;
}

function createEvent(
    incomingHeaders: Record<string, string>,
    backendResponse: Response = new Response(null)
): FakeEvent {
    const fetchMock = vi.fn<typeof fetch>().mockResolvedValue(backendResponse);
    const setCookieMock = vi.fn();
    const event = {
        request: new Request('http://frontend.test/', { headers: incomingHeaders }),
        fetch: fetchMock,
        cookies: { set: setCookieMock }
    } as unknown as RequestEvent;
    return { event, fetchMock, setCookieMock };
}

function sentHeaders(fetchMock: Mock<typeof fetch>): Headers {
    const init: RequestInit | undefined = fetchMock.mock.calls[0]?.[1];
    return new Headers(init?.headers);
}

describe('backendFetch', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should forward the incoming Accept-Language header to the backend', async () => {
        const { event, fetchMock } = createEvent({ 'accept-language': 'de-DE,de;q=0.9' });

        await backendFetch(event)(BACKEND_URL);

        expect(sentHeaders(fetchMock).get('accept-language')).toBe('de-DE,de;q=0.9');
    });

    it('should not set Accept-Language when the incoming request has none', async () => {
        const { event, fetchMock } = createEvent({});

        await backendFetch(event)(BACKEND_URL);

        expect(sentHeaders(fetchMock).has('accept-language')).toBe(false);
    });

    it('should keep an Accept-Language header set explicitly via init', async () => {
        const { event, fetchMock } = createEvent({ 'accept-language': 'de' });

        await backendFetch(event)(BACKEND_URL, { headers: { 'accept-language': 'fr' } });

        expect(sentHeaders(fetchMock).get('accept-language')).toBe('fr');
    });

    it('should keep an Accept-Language header set explicitly on a Request input', async () => {
        const { event, fetchMock } = createEvent({ 'accept-language': 'de' });
        const request = new Request(BACKEND_URL, { headers: { 'accept-language': 'fr' } });

        await backendFetch(event)(request);

        expect(sentHeaders(fetchMock).get('accept-language')).toBe('fr');
    });

    it('should preserve other headers from init and from a Request input', async () => {
        const first = createEvent({ 'accept-language': 'de' });
        await backendFetch(first.event)(BACKEND_URL, { headers: { authorization: 'Bearer a' } });
        expect(sentHeaders(first.fetchMock).get('authorization')).toBe('Bearer a');
        expect(sentHeaders(first.fetchMock).get('accept-language')).toBe('de');

        const second = createEvent({ 'accept-language': 'de' });
        const request = new Request(BACKEND_URL, { headers: { authorization: 'Bearer b' } });
        await backendFetch(second.event)(request);
        expect(sentHeaders(second.fetchMock).get('authorization')).toBe('Bearer b');
        expect(sentHeaders(second.fetchMock).get('accept-language')).toBe('de');
    });

    it('should still replay the backend Set-Cookie headers onto the response', async () => {
        const backendResponse = new Response(null, {
            headers: { 'set-cookie': 'session=abc; Path=/; SameSite=lax' }
        });
        const { event, setCookieMock } = createEvent({}, backendResponse);

        await backendFetch(event)(BACKEND_URL);

        expect(setCookieMock).toHaveBeenCalledWith(
            'session',
            'abc',
            expect.objectContaining({ path: '/', sameSite: 'lax' })
        );
    });
});
