import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { isLanguageCode } from '$lib/helper/language-code';

describe('isLanguageCode', () => {
    it('recognizes an ISO 639-1 code', () => {
        expect(isLanguageCode('de')).toBe(true);
        expect(isLanguageCode('en')).toBe(true);
        expect(isLanguageCode('fr')).toBe(true);
    });

    it('recognizes an ISO 639-3 code', () => {
        expect(isLanguageCode('deu')).toBe(true);
        expect(isLanguageCode('eng')).toBe(true);
    });

    it('is case-insensitive', () => {
        expect(isLanguageCode('DE')).toBe(true);
        expect(isLanguageCode('De')).toBe(true);
    });

    it('rejects a route name that is not a language code', () => {
        expect(isLanguageCode('imprint')).toBe(false);
        expect(isLanguageCode('login')).toBe(false);
        expect(isLanguageCode('')).toBe(false);
    });
});
