import type { Cookies } from '@sveltejs/kit';

import type { Locale } from '$paraglide/runtime';
import { isLocale } from '$paraglide/runtime';

export const LANGUAGE_COOKIE_NAME = 'language';

const LANGUAGE_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 365;

/**
 * @brief Reads the website language that the visitor explicitly chose.
 * The cookie is not trusted: a value that is not a UI language is ignored, as if no choice was made.
 *
 * @param cookies the cookies of the request
 * @returns the chosen UI language, or undefined if there is no valid choice
 */
export function getLanguageCookie(cookies: Cookies): Locale | undefined {
    const value = cookies.get(LANGUAGE_COOKIE_NAME);
    return value !== undefined && isLocale(value) ? value : undefined;
}

/**
 * @brief Stores the website language that the visitor explicitly chose.
 * The cookie holds no sensitive data. It is not readable by scripts, because the server reads it.
 *
 * Only a UI language can be stored, so that `getLanguageCookie` never has to ignore a value that this function wrote.
 *
 * @param cookies the cookies of the response
 * @param language the chosen UI language
 * @throws Error if `language` is not a UI language
 */
export function setLanguageCookie(cookies: Cookies, language: string): void {
    if (!isLocale(language)) {
        throw new Error(`"${language}" is not a UI language.`);
    }
    cookies.set(LANGUAGE_COOKIE_NAME, language, {
        path: '/',
        maxAge: LANGUAGE_COOKIE_MAX_AGE_SECONDS,
        httpOnly: true,
        sameSite: 'lax'
    });
}
