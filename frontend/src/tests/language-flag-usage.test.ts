import { readFileSync } from 'node:fs';
import path from 'node:path';

import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';

import { languageTagToFlagCountryCode } from '$lib/helper/language-flag';

import { locales } from '$paraglide/runtime';

const LANGUAGE_SELECT_FILE = path.resolve(
    import.meta.dirname,
    '../lib/elements/switch/LanguageSelect.svelte'
);

const SNIPPET_PATTERN = /\{#snippet (\w+)\([^)]*\)\}([\s\S]*?)\{\/snippet\}/g;
const FLAG_CLASS_PATTERN = /class:fi-([a-z]{2})=/g;

/**
 * @brief Finds the flag-icons country codes that each `{#snippet ...}` in `LanguageSelect.svelte`
 * hardcodes a `class:fi-<code>` for. `class:` needs a literal class name, so it cannot be built from a
 * variable; this is, per snippet, the list that would have to grow whenever a configured UI language
 * needs a flag that snippet does not already render.
 *
 * @returns the country codes rendered by each snippet, keyed by the snippet's name
 */
function findRenderedFlagCountryCodesBySnippet(): Record<string, string[]> {
    const source = readFileSync(LANGUAGE_SELECT_FILE, 'utf-8');
    const codesBySnippet: Record<string, string[]> = {};

    for (const [, name, body] of source.matchAll(SNIPPET_PATTERN)) {
        if (name === undefined || body === undefined) {
            continue;
        }

        const codes: string[] = [];
        for (const [, code] of body.matchAll(FLAG_CLASS_PATTERN)) {
            if (code !== undefined) {
                codes.push(code);
            }
        }
        codesBySnippet[name] = codes;
    }

    return codesBySnippet;
}

/**
 * @brief Finds the required flag country codes missing from at least one icon snippet.
 * @param codesBySnippet the country codes rendered by each snippet, keyed by the snippet's name
 * @returns the missing country codes, e.g. `['gb']`
 */
function findMissingFlagCountryCodes(codesBySnippet: Record<string, string[]>): string[] {
    const requiredCodes = locales.map(languageTagToFlagCountryCode);
    const missingCodes = new Set<string>();
    for (const codes of Object.values(codesBySnippet)) {
        for (const requiredCode of requiredCodes) {
            if (!codes.includes(requiredCode)) {
                missingCodes.add(requiredCode);
            }
        }
    }
    return [...missingCodes];
}

describe('LanguageSelect flag classes', () => {
    const codesBySnippet = findRenderedFlagCountryCodesBySnippet();

    it('finds the icon snippets', () => {
        expect(Object.keys(codesBySnippet).length).toBeGreaterThan(0);
    });

    it('hardcodes a flag class for every configured UI language, in every icon snippet', () => {
        const missingCodes = findMissingFlagCountryCodes(codesBySnippet);

        expect(
            missingCodes,
            `Missing flag class in LanguageSelect. Missing flags: ${missingCodes.join(', ')}`
        ).toEqual([]);
    });
});
