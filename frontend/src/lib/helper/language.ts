import type { RequestEvent } from '@sveltejs/kit';

/**
 * @brief A language tag that only `withLanguage` creates. A plain string does not fit, so the compiler
 * rejects a language that was written into the page data by hand.
 */
export type LanguageTag = string & { readonly __brand: 'LanguageTag' };

export const DEFAULT_LANGUAGE_TAG = 'en';

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
    event.locals.languageTag = languageTag;
    return { ...data, languageTag: languageTag as LanguageTag } as T & { languageTag: LanguageTag };
}
