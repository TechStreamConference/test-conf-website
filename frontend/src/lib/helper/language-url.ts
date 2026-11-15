import { isLanguageCode } from '$lib/helper/language-code';

export interface StrippedLanguagePrefix {
    languageCode: string | undefined;
    rest: string;
}

/**
 * @brief Splits a path into its leading language code, if any, and the rest of the path without it.
 * Used both to route a language-prefixed path and to build one, so both recognize the same prefixes.
 * @param pathname an absolute path, e.g. `/de/imprint` or `/imprint`.
 * @returns the language code (undefined if the path has none) and the remaining path.
 */
export function stripLanguagePrefix(pathname: string): StrippedLanguagePrefix {
    const segments = pathname.split('/');
    const firstSegment = segments[1];
    const hasLanguagePrefix = firstSegment !== undefined && isLanguageCode(firstSegment);
    const rest = (hasLanguagePrefix ? segments.slice(2) : segments.slice(1)).join('/');
    return { languageCode: hasLanguagePrefix ? firstSegment : undefined, rest };
}

/**
 * @brief Rewrites a path so it starts with the given language, replacing an existing language prefix if
 * there is one (e.g. `/de/imprint` + `en` becomes `/en/imprint`, and `/fr/imprint` + `de` becomes
 * `/de/imprint`, even though `fr` is not a language this site's UI offers).
 * @param pathname the current path, e.g. `/imprint` or `/de/imprint`.
 * @param languageTag the language to prefix the path with.
 * @returns the path with exactly one language prefix.
 */
export function withLanguagePrefix(pathname: string, languageTag: string): string {
    const { rest } = stripLanguagePrefix(pathname);
    return rest === '' ? `/${languageTag}` : `/${languageTag}/${rest}`;
}
