import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { stripLanguagePrefix } from '$lib/helper/language-url';
import { withLanguagePrefix } from '$lib/helper/language-url';

describe('stripLanguagePrefix', () => {
    it('finds a language code at the start of the path', () => {
        expect(stripLanguagePrefix('/de/imprint')).toEqual({ languageCode: 'de', rest: 'imprint' });
        expect(stripLanguagePrefix('/de')).toEqual({ languageCode: 'de', rest: '' });
    });

    it('finds any ISO 639 code, not only a supported UI language', () => {
        expect(stripLanguagePrefix('/fr/imprint')).toEqual({ languageCode: 'fr', rest: 'imprint' });
    });

    it('finds nothing without a language code at the start', () => {
        expect(stripLanguagePrefix('/imprint')).toEqual({
            languageCode: undefined,
            rest: 'imprint'
        });
        expect(stripLanguagePrefix('/')).toEqual({ languageCode: undefined, rest: '' });
    });

    it('only looks at the first segment', () => {
        expect(stripLanguagePrefix('/imprint/de')).toEqual({
            languageCode: undefined,
            rest: 'imprint/de'
        });
    });
});

describe('withLanguagePrefix', () => {
    it('adds the language prefix to a path without one', () => {
        expect(withLanguagePrefix('/imprint', 'de')).toBe('/de/imprint');
        expect(withLanguagePrefix('/', 'de')).toBe('/de');
    });

    it('replaces an existing language prefix instead of stacking another one', () => {
        expect(withLanguagePrefix('/de/imprint', 'en')).toBe('/en/imprint');
        expect(withLanguagePrefix('/fr/imprint', 'de')).toBe('/de/imprint');
    });
});
