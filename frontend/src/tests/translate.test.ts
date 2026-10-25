import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { i18n } from '$lib/helper/translate';
import { normalizeLanguageTag } from '$lib/helper/translate';
import { toLanguageTag } from '$lib/helper/language';

import { m } from '$paraglide/messages';

// The expected texts come from Paraglide itself, so these tests do not depend on the wording of the messages.
const GERMAN_TEXT = m.test_plain({}, { locale: 'de' });
const ENGLISH_TEXT = m.test_plain({}, { locale: 'en' });

describe('normalizeLanguageTag', () => {
    it('should keep a supported language', () => {
        expect(normalizeLanguageTag('de')).toBe('de');
        expect(normalizeLanguageTag('en')).toBe('en');
    });

    it('should lowercase the tag', () => {
        expect(normalizeLanguageTag('DE')).toBe('de');
        expect(normalizeLanguageTag('EN')).toBe('en');
    });

    it('should reduce a tag with a region to its language', () => {
        expect(normalizeLanguageTag('de-AT')).toBe('de');
        expect(normalizeLanguageTag('en-US')).toBe('en');
        expect(normalizeLanguageTag('EN-gb')).toBe('en');
    });

    it('should not check the language against the supported languages', () => {
        expect(normalizeLanguageTag('fr')).toBe('fr');
        expect(normalizeLanguageTag('fr-CA')).toBe('fr');
    });

    it('should return an empty tag as it is', () => {
        expect(normalizeLanguageTag('')).toBe('');
    });
});

describe('i18n', () => {
    it('should use different texts for the languages, otherwise the other tests prove nothing', () => {
        expect(GERMAN_TEXT).not.toBe(ENGLISH_TEXT);
    });

    it('should render the text of a supported language', () => {
        expect(i18n(m.test_plain, 'de')).toBe(GERMAN_TEXT);
        expect(i18n(m.test_plain, 'en')).toBe(ENGLISH_TEXT);
    });

    it('should ignore the case of the language tag', () => {
        expect(i18n(m.test_plain, 'DE')).toBe(GERMAN_TEXT);
    });

    it('should use the language of a tag with a region', () => {
        expect(i18n(m.test_plain, 'de-AT')).toBe(GERMAN_TEXT);
        expect(i18n(m.test_plain, 'en-US')).toBe(ENGLISH_TEXT);
    });

    it('should fall back to the base language for an unsupported language', () => {
        expect(i18n(m.test_plain, 'fr')).toBe(ENGLISH_TEXT);
    });

    it('should fall back to the base language for an empty tag', () => {
        expect(i18n(m.test_plain, '')).toBe(ENGLISH_TEXT);
    });

    it('should fill in the placeholders in every language', () => {
        const inputs = { placeholder1: 'first', placeholder2: 'second' };

        for (const languageTag of ['de', 'en']) {
            const text = i18n(m.test_withPlaceholder, languageTag, inputs);

            expect(text).toContain('first');
            expect(text).toContain('second');
            expect(text).not.toContain('undefined');
        }
    });

    it('should fill in the placeholders of the fallback language', () => {
        const inputs = { placeholder1: 'first', placeholder2: 'second' };

        expect(i18n(m.test_withPlaceholder, 'fr', inputs)).toBe(
            m.test_withPlaceholder(inputs, { locale: 'en' })
        );
    });
});

// The language of a page goes through `toLanguageTag` first, so `i18n` has to handle what it returns.
describe('i18n with a checked language tag', () => {
    it('should render the text for the canonical form of a tag with a region', () => {
        expect(i18n(m.test_plain, toLanguageTag('de-de'))).toBe(GERMAN_TEXT);
        expect(i18n(m.test_plain, toLanguageTag('en-us'))).toBe(ENGLISH_TEXT);
    });

    it('should use the language of a tag with a script and a region', () => {
        expect(i18n(m.test_plain, toLanguageTag('de-Latn-DE'))).toBe(GERMAN_TEXT);
    });

    it('should fall back to the base language for a valid tag of an unsupported language', () => {
        expect(i18n(m.test_plain, toLanguageTag('zh-Hant'))).toBe(ENGLISH_TEXT);
        expect(i18n(m.test_plain, toLanguageTag('es-419'))).toBe(ENGLISH_TEXT);
    });

    it('should render the text for a locale written with an underscore', () => {
        expect(i18n(m.test_plain, toLanguageTag('de_DE'))).toBe(GERMAN_TEXT);
    });

    it('should fall back to the base language for a tag that is not valid', () => {
        expect(i18n(m.test_plain, toLanguageTag('"><script>'))).toBe(ENGLISH_TEXT);
        expect(i18n(m.test_plain, toLanguageTag(''))).toBe(ENGLISH_TEXT);
    });
});
