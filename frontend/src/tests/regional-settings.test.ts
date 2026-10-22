import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { toReportableLocale } from '$lib/helper/regional_settings';

const RESOLVED_LOCALE = Intl.DateTimeFormat().resolvedOptions().locale;

describe('toReportableLocale', () => {
    it('canonicalizes a well-formed language', () => {
        expect(toReportableLocale('en-us')).toBe('en-US');
        expect(toReportableLocale('DE-de')).toBe('de-DE');
        expect(toReportableLocale('zh-hant-tw')).toBe('zh-Hant-TW');
    });

    it('keeps a well-formed language the browser has no data for', () => {
        expect(toReportableLocale('abc-123')).toBe('abc-123');
    });

    it('falls back to the resolved locale for a malformed language', () => {
        expect(toReportableLocale('en_US')).toBe(RESOLVED_LOCALE);
        expect(toReportableLocale('')).toBe(RESOLVED_LOCALE);
        expect(toReportableLocale('x')).toBe(RESOLVED_LOCALE);
    });

    it('keeps a canonical language of exactly 64 characters', () => {
        const language = 'en-x-' + 'abcdefg-'.repeat(7) + 'abc';
        expect(language).toHaveLength(64);
        expect(toReportableLocale(language)).toBe(language);
    });

    it('falls back to the resolved locale for a canonical language longer than 64 characters', () => {
        const language = 'en-x-' + 'abcdefg-'.repeat(7) + 'abcd';
        expect(language).toHaveLength(65);
        expect(toReportableLocale(language)).toBe(RESOLVED_LOCALE);
    });
});
