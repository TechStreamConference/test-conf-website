import { iso6393 } from 'iso-639-3';

// Both ISO 639-1 (2-letter, e.g. `de`) and ISO 639-3 (3-letter, e.g. `deu`) codes, since a path
// segment could be either, whether or not this site's UI actually supports that language.
const LANGUAGE_CODES: ReadonlySet<string> = new Set(
    iso6393
        .flatMap((language) => [language.iso6391, language.iso6393])
        .filter((code) => code !== undefined)
);

/**
 * @brief Checks whether a path segment is a language code, not whether this site's UI supports it.
 * A hook strips such a segment from the path before it reaches the router, so our own URL rewriting
 * has to recognize the same segments, including ones we do not (yet) offer as a UI language.
 * @param segment the path segment to check, e.g. `de` or `imprint`.
 * @returns true if the segment is a known ISO 639-1 or ISO 639-3 language code.
 */
export function isLanguageCode(segment: string): boolean {
    return LANGUAGE_CODES.has(segment.toLowerCase());
}
