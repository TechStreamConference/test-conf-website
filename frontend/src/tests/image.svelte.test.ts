import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';
import { render } from 'vitest-browser-svelte';

import { warnIfBothImageDimensionsSet } from '$lib/helper/runtime-checks';
import Image from '$lib/elements/img/Image.svelte';

vi.mock('$lib/helper/runtime-checks', () => ({
    warnIfBothImageDimensionsSet: vi.fn()
}));

describe('Image', () => {
    it('runs the dimension check with the given props on mount', async () => {
        await render(Image, { src: '/logo.png', alt: 'Logo', height: '10rem', width: '20rem' });

        expect(warnIfBothImageDimensionsSet).toHaveBeenCalledWith('10rem', '20rem', '/logo.png');
    });

    it('runs the dimension check with undefined for the dimensions that were not set', async () => {
        await render(Image, { src: '/logo.png', alt: 'Logo' });

        expect(warnIfBothImageDimensionsSet).toHaveBeenCalledWith(
            undefined,
            undefined,
            '/logo.png'
        );
    });
});
