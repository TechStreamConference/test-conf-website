import type { RequestEvent } from '@sveltejs/kit';

/**
 * @brief A language tag that only `withLanguage` creates. A plain string does not fit, so the compiler
 * rejects a language that was written into the page data by hand.
 */
export type LanguageTag = string & { readonly __brand: 'LanguageTag' };

export const DEFAULT_LANGUAGE_TAG = 'en';

/**
 * @brief Brings a language tag into its canonical form (`de-de` becomes `de-DE`). The result only
 * contains letters, digits and hyphens, so it is safe to put into the `lang` attribute of the html.
 * An underscore is accepted instead of the hyphen (`de_DE`), because that is a common way to write a locale.
 * Only the structure of the tag is checked, not whether the language exists. That is up to the backend.
 *
 * @param languageTag the language tag to check
 * @returns the canonical language tag, or the default if the structure is not valid
 */
export function toLanguageTag(languageTag: string): string {
    try {
        return (
            Intl.getCanonicalLocales(languageTag.replaceAll('_', '-'))[0] ?? DEFAULT_LANGUAGE_TAG
        );
    } catch {
        return DEFAULT_LANGUAGE_TAG;
    }
}

/**
 * @brief Sets the language of the current request and adds it to the page data. The server renders the
 * `lang` attribute from the request, the layout reads the page data, and this keeps both the same.
 *
 * @param event the request event of the `load` function
 * @param languageTag the language tag of the page
 * @param data the other data the `load` function returns
 * @returns the given data together with the language tag
 */
export function withLanguage<T extends object>(
    event: RequestEvent,
    languageTag: string,
    data?: T & { languageTag?: never }
): T & { languageTag: LanguageTag } {
    const checkedLanguageTag = toLanguageTag(languageTag);
    event.locals.languageTag = checkedLanguageTag;
    return { ...data, languageTag: checkedLanguageTag as LanguageTag } as T & {
        languageTag: LanguageTag;
    };
}

/**
 * @brief Sets the given language for the request, unless a `load` function already set one.
 * The check and the write happen without an `await` in between, so no other `load` function can run
 * between them, whichever one is faster.
 *
 * @see withLanguage
 *
 * @param event the request event of the `load` function
 * @param languageTag the language to set, e.g. from the user setting. The default if undefined.
 * @param data the other data the `load` function returns
 * @returns the given data together with the language that applies to the request, which is the one that
 * was already set or else the given one
 */
export function withDefaultLanguage<T extends object>(
    event: RequestEvent,
    languageTag?: string,
    data?: T & { languageTag?: never }
): T & { languageTag: LanguageTag } {
    event.locals.languageTag ??= toLanguageTag(languageTag ?? DEFAULT_LANGUAGE_TAG);
    return { ...data, languageTag: event.locals.languageTag as LanguageTag } as T & {
        languageTag: LanguageTag;
    };
}
