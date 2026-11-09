import type { RequestEvent } from '@sveltejs/kit';

import { beforeEach } from 'vitest';
import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

import { loadGlobals } from '$bff/v1/globals.server';

import { getGlobalsV1 } from '$gen/sdk.gen';

vi.mock('$logging', () => ({
    logger: { info: vi.fn() }
}));
vi.mock('$bff/client', () => ({
    backendFetch: vi.fn(() => fetch)
}));
vi.mock('$gen/sdk.gen', () => ({
    getGlobalsV1: vi.fn(() =>
        Promise.resolve({ data: { footerText: 'Footer text' }, response: new Response() })
    )
}));

function createRequestEvent(cookies: Record<string, string>): RequestEvent {
    return { cookies: { get: (name: string) => cookies[name] } } as unknown as RequestEvent;
}

describe('loadGlobals', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('asks for the language that the visitor chose', async () => {
        await loadGlobals(createRequestEvent({ language: 'de' }));

        expect(getGlobalsV1).toHaveBeenCalledWith(
            expect.objectContaining({ query: { language: 'de' } })
        );
    });

    it('asks for no language without a choice, so the backend negotiates it', async () => {
        await loadGlobals(createRequestEvent({}));

        expect(getGlobalsV1).toHaveBeenCalledWith(expect.objectContaining({ query: {} }));
    });

    it('does not override the stored language of a logged-in user', async () => {
        await loadGlobals(createRequestEvent({ language: 'de', '__Host-session': 'token' }));

        expect(getGlobalsV1).toHaveBeenCalledWith(expect.objectContaining({ query: {} }));
    });
});
