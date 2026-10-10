import type { RequestEvent } from '@sveltejs/kit';

import { expect } from 'vitest';
import { it } from 'vitest';

import { withLanguage } from '$lib/helper/language';

import type { PageServerLoad } from '../routes/auth/callback/$types';

// Note: the `@ts-expect-error` directives are verified by `svelte-check` (`just frontend-check`), not by vitest.

it('accepts a page that does not set a language', () => {
    const load: PageServerLoad = () => ({});

    expect(load).toBeTypeOf('function');
});

it('accepts the result of withLanguage', () => {
    const load: PageServerLoad = (event: RequestEvent) => withLanguage(event, 'de', { value: 1 });

    expect(load).toBeTypeOf('function');
});

it('rejects a language tag that was written by hand', () => {
    // @ts-expect-error A plain string is not a LanguageTag, only `withLanguage` creates one.
    const load: PageServerLoad = () => ({ languageTag: 'en' });

    expect(load).toBeTypeOf('function');
});

it('rejects a language tag in the data of withLanguage', () => {
    // @ts-expect-error The data must not contain a language tag, `withLanguage` sets it.
    const withTag = (event: RequestEvent) => withLanguage(event, 'de', { languageTag: 'en' });

    expect(withTag).toBeTypeOf('function');
});
