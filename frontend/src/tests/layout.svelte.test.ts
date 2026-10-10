import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { createRawSnippet } from 'svelte';
import { render } from 'vitest-browser-svelte';

import { MAIN_PAGE_FOOTER_MENU } from '$lib/helper/menus';
import { MAIN_PAGE_HEADER_MENU } from '$lib/helper/menus';
import BasePage from '$lib/elements/layout/BasePage.svelte';
import { UserState } from '$lib/helper/menus';

const FOOTER_TEXT = 'Footer text from the backend';

async function renderPage(languageTag: string) {
    // `events` is also the name of a Svelte option, so the props have to be under `props`.
    return await render(BasePage, {
        props: {
            children: createRawSnippet(() => ({ render: () => '<p>Page content</p>' })),
            languageTag,
            userState: UserState.LoggedOut,
            headerMenu: MAIN_PAGE_HEADER_MENU,
            footerMenu: MAIN_PAGE_FOOTER_MENU,
            events: [{ label: '2026', url: '/year/2026' }],
            footerText: FOOTER_TEXT
        }
    });
}

describe('base page language', () => {
    it('shows the English headlines of the footer', async () => {
        const screen = await renderPage('en');

        await expect.element(screen.getByRole('heading', { name: 'Menu' })).toBeVisible();
        await expect.element(screen.getByRole('heading', { name: 'All Events' })).toBeVisible();
    });

    it('shows the German headlines of the footer', async () => {
        const screen = await renderPage('de');

        await expect.element(screen.getByRole('heading', { name: 'Menü' })).toBeVisible();
        await expect.element(screen.getByRole('heading', { name: 'Alle Events' })).toBeVisible();
    });

    it('shows the content of the page and the footer text unchanged in every language', async () => {
        const screen = await renderPage('de');

        await expect.element(screen.getByText('Page content')).toBeVisible();
        await expect.element(screen.getByText(FOOTER_TEXT)).toBeVisible();
    });
});
