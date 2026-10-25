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
    event.locals.languageTag ??= languageTag ?? DEFAULT_LANGUAGE_TAG;
    return { ...data, languageTag: event.locals.languageTag as LanguageTag } as T & {
        languageTag: LanguageTag;
    };
}
