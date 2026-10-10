import type { RequestEvent } from '@sveltejs/kit';

import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { readFileSync } from 'node:fs';
import path from 'node:path';
import { vi } from 'vitest';

import { getCurrentUser } from '$bff/v1/auth.server';
import { GenericBackendError } from '$bff/errors';

import type { MeResponseV1 } from '$gen/types.gen';

import { DEFAULT_LANGUAGE_TAG } from '$lib/helper/language';
import { withLanguage } from '$lib/helper/language';
import { UserState } from '$lib/helper/menus';

import { handle } from '../hooks.server';
import { load as loadLayout } from '../routes/+layout.server';

vi.mock('$bff/v1/globals.server', () => ({
    loadGlobals: vi.fn(() => Promise.resolve({ footerText: 'Footer text' }))
}));
vi.mock('$bff/v1/auth.server', () => ({
    getCurrentUser: vi.fn(() => Promise.resolve({ ok: false, status: 401 }))
}));

const APP_HTML = path.resolve(import.meta.dirname, '../app.html');
const HTML_WITH_PLACEHOLDER = '<html lang="%lang%">';

function createEvent(): RequestEvent {
    return {
        locals: { languageTag: '' },
        request: new Request('http://localhost/'),
        url: new URL('http://localhost/')
    } as unknown as RequestEvent;
}

interface LayoutData {
    languageTag: string;
    userState: UserState;
    user: MeResponseV1 | null;
    footerText: string;
}

/**
 * @brief Runs the root layout `load` the way SvelteKit does.
 *
 * @param event the request event
 * @returns the data of the layout
 * @throws Error if the layout `load` returns nothing
 */
async function runLayoutLoad(event: RequestEvent): Promise<LayoutData> {
    const data = await loadLayout(event as unknown as Parameters<typeof loadLayout>[0]);
    if (data === undefined) {
        throw new Error('The layout load returned nothing.');
    }
    return data as unknown as LayoutData;
}

/**
 * @brief Handles a request. The `load` functions run before the page is rendered, so `runLoads` runs
 * first and the html is transformed afterwards, the same order SvelteKit uses.
 *
 * @param event the request event
 * @param runLoads the `load` functions of the request
 * @returns the html with the `lang` attribute filled in
 */
async function renderHtml(event: RequestEvent, runLoads: () => Promise<void>): Promise<string> {
    const response = await handle({
        event,
        resolve: async (_event, options) => {
            await runLoads();
            const html = await options?.transformPageChunk?.({
                html: HTML_WITH_PLACEHOLDER,
                done: true
            });
            return new Response(html);
        }
    });
    return await response.text();
}

describe('withLanguage', () => {
    it('sets the language of the request and returns it with the data', () => {
        const event = createEvent();

        const data = withLanguage(event, 'de', { title: 'Hello' });

        expect(event.locals.languageTag).toBe('de');
        expect(data).toEqual({ title: 'Hello', languageTag: 'de' });
    });

    it('returns only the language without data', () => {
        const event = createEvent();

        expect(withLanguage(event, 'de')).toEqual({ languageTag: 'de' });
    });

    it('does not change the given data', () => {
        const data = Object.freeze({ title: 'Hello' });

        const result = withLanguage(createEvent(), 'de', data);

        expect(data).toEqual({ title: 'Hello' });
        expect(result).not.toBe(data);
    });
});

describe('lang attribute of the html', () => {
    it('contains the placeholder the hook replaces', () => {
        expect(readFileSync(APP_HTML, 'utf-8')).toContain(HTML_WITH_PLACEHOLDER);
    });

    it('is the default language when no page sets one', async () => {
        const event = createEvent();

        const html = await renderHtml(event, async () => {
            await runLayoutLoad(event);
        });

        expect(html).toBe(`<html lang="${DEFAULT_LANGUAGE_TAG}">`);
    });

    it('is the language of the page when it overrides the layout', async () => {
        const event = createEvent();

        const html = await renderHtml(event, async () => {
            await runLayoutLoad(event);
            withLanguage(event, 'de');
        });

        expect(html).toBe('<html lang="de">');
    });

    it('starts every request with the default language', async () => {
        const event = createEvent();
        event.locals.languageTag = 'de';

        const html = await renderHtml(event, () => Promise.resolve());

        expect(html).toBe(`<html lang="${DEFAULT_LANGUAGE_TAG}">`);
    });
});

describe('root layout load', () => {
    it('returns the default language and sets it for the request', async () => {
        const event = createEvent();

        const data = await runLayoutLoad(event);

        expect(data.languageTag).toBe(DEFAULT_LANGUAGE_TAG);
        expect(event.locals.languageTag).toBe(DEFAULT_LANGUAGE_TAG);
    });

    it('is overridden by the language data of a page', async () => {
        const event = createEvent();

        const layoutData = await runLayoutLoad(event);
        const pageData = withLanguage(event, 'de', { title: 'Hello' });

        // SvelteKit merges the data of the layouts and the page, the deeper one wins.
        expect({ ...layoutData, ...pageData }.languageTag).toBe('de');
    });

    it('forwards the footer text of the globals', async () => {
        const data = await runLayoutLoad(createEvent());

        expect(data.footerText).toBe('Footer text');
    });

    it('is logged out and has no user when the backend answers with 401', async () => {
        const data = await runLayoutLoad(createEvent());

        expect(data.userState).toBe(UserState.LoggedOut);
        expect(data.user).toBeNull();
    });

    it('is logged in and has the user when the backend returns one', async () => {
        const user = { id: 1, username: 'alice' } as unknown as MeResponseV1;
        vi.mocked(getCurrentUser).mockResolvedValueOnce({ ok: true, data: user });

        const data = await runLayoutLoad(createEvent());

        expect(data.userState).toBe(UserState.LoggedIn);
        expect(data.user).toEqual(user);
    });

    it('fails on a backend error that is not a 401', async () => {
        vi.mocked(getCurrentUser).mockResolvedValueOnce({ ok: false, status: 500 });

        await expect(runLayoutLoad(createEvent())).rejects.toBeInstanceOf(GenericBackendError);
    });
});
