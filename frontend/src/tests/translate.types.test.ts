import { expect } from 'vitest';
import { it } from 'vitest';

import { i18n } from '$lib/helper/translate';

import { m } from '$paraglide/messages';

// Note: the `@ts-expect-error` directives are verified by `svelte-check` (`just frontend-check`), not by vitest.

it('accepts a message without placeholders and without inputs', () => {
    const render = () => i18n(m.test_plain, 'de');

    expect(render).toBeTypeOf('function');
});

it('accepts a message with exactly its placeholders', () => {
    const render = () => i18n(m.test_withPlaceholder, 'de', { placeholder1: 1, placeholder2: 2 });

    expect(render).toBeTypeOf('function');
});

it('rejects a message with a missing placeholder', () => {
    // @ts-expect-error The message needs `placeholder2` as well.
    const render = () => i18n(m.test_withPlaceholder, 'de', { placeholder1: 1 });

    expect(render).toBeTypeOf('function');
});

it('rejects a message with placeholders and without inputs', () => {
    // @ts-expect-error The message needs its placeholders.
    const render = () => i18n(m.test_withPlaceholder, 'de');

    expect(render).toBeTypeOf('function');
});

it('rejects an extra property for a message without placeholders', () => {
    // @ts-expect-error The message has no placeholder `foo`.
    const render = () => i18n(m.test_plain, 'de', { foo: 1 });

    expect(render).toBeTypeOf('function');
});

it('rejects an extra property for a message with placeholders', () => {
    const inputs = { placeholder1: 1, placeholder2: 2, foo: 3 };
    // @ts-expect-error The message has no placeholder `foo`.
    const render = () => i18n(m.test_withPlaceholder, 'de', inputs);

    expect(render).toBeTypeOf('function');
});
