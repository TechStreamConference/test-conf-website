import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';
import { createRawSnippet } from 'svelte';
import { render } from 'vitest-browser-svelte';

const { mockPage } = vi.hoisted(() => ({
    mockPage: { url: new URL('https://example.com/imprint') }
}));

vi.mock('$app/state', () => ({ page: mockPage }));

import InlineLink from '$lib/elements/link/InlineLink.svelte';
import Link from '$lib/elements/link/Link.svelte';

function children(text: string) {
    return createRawSnippet(() => ({ render: () => `<span>${text}</span>` }));
}

describe.each([
    { name: 'Link', component: Link },
    { name: 'InlineLink', component: InlineLink }
])('$name', ({ component }) => {
    it('keeps an internal href unchanged when the current URL has no language prefix', async () => {
        mockPage.url = new URL('https://example.com/imprint');

        const screen = await render(component, {
            props: { href: '/imprint', 'aria-label': 'Imprint', children: children('Imprint') }
        });

        await expect
            .element(screen.getByRole('link', { name: 'Imprint' }))
            .toHaveAttribute('href', '/imprint');
    });

    it('adds the current URL’s language prefix to an internal href', async () => {
        mockPage.url = new URL('https://example.com/de/imprint');

        const screen = await render(component, {
            props: { href: '/events', 'aria-label': 'Events', children: children('Events') }
        });

        await expect
            .element(screen.getByRole('link', { name: 'Events' }))
            .toHaveAttribute('href', '/de/events');
    });

    it('leaves an external href alone, even with a language prefix on the current URL', async () => {
        mockPage.url = new URL('https://example.com/de/imprint');

        const screen = await render(component, {
            props: {
                href: 'https://github.com/TechStreamConference',
                'aria-label': 'GitHub',
                children: children('GitHub')
            }
        });

        await expect
            .element(screen.getByRole('link', { name: 'GitHub' }))
            .toHaveAttribute('href', 'https://github.com/TechStreamConference');
    });
});
