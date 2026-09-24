import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

import { warnIfBothImageDimensionsSet } from '$lib/helper/runtime-checks';

describe('warnIfBothImageDimensionsSet', () => {
    it('should warn when both height and width are set', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
        warnIfBothImageDimensionsSet('10rem', '20rem', '/logo.png');
        expect(warnSpy).toHaveBeenCalledOnce();
        expect(warnSpy.mock.calls[0]?.[1]).toBe('/logo.png');
        warnSpy.mockRestore();
    });

    it('should not warn when only the height is set', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
        warnIfBothImageDimensionsSet('10rem', undefined, '/logo.png');
        expect(warnSpy).not.toHaveBeenCalled();
        warnSpy.mockRestore();
    });

    it('should not warn when only the width is set', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
        warnIfBothImageDimensionsSet(undefined, '20rem', '/logo.png');
        expect(warnSpy).not.toHaveBeenCalled();
        warnSpy.mockRestore();
    });

    it('should not warn when neither dimension is set', () => {
        const warnSpy = vi.spyOn(console, 'warn').mockImplementation(() => undefined);
        warnIfBothImageDimensionsSet(undefined, undefined, '/logo.png');
        expect(warnSpy).not.toHaveBeenCalled();
        warnSpy.mockRestore();
    });
});
