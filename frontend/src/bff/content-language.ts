import type { RequestEvent } from '@sveltejs/kit';

import type { Locale } from '$paraglide/runtime';

import { getLanguageCookie } from '$lib/helper/language-cookie.server';

// Mirrors `SESSION_COOKIE_NAME` in the backend's `session.py`.
const SESSION_COOKIE_NAME = '__Host-session';

/**
 * @brief Returns the website language that the visitor chose, but only for a visitor who is not logged in.
 * The backend stores the language of a logged-in user and picks it by itself.
 * A language that we send to the backend would replace the stored one, so we return nothing for a logged-in user.
 *
 * @param event the request event
 * @returns the chosen UI language, or undefined if the backend negotiates the language
 */
export function getExplicitLanguage(event: RequestEvent): Locale | undefined {
    if (event.cookies.get(SESSION_COOKIE_NAME) !== undefined) {
        return undefined;
    }
    return getLanguageCookie(event.cookies);
}

/**
 * @brief Builds the query for a backend call that returns content in one language.
 * If the visitor chose a language, the query asks the backend for exactly this language.
 * If not, the query is empty and the backend picks the language by itself.
 *
 * @see getExplicitLanguage
 *
 * @param event the request event
 * @returns a query with the `language` parameter, or an empty query
 */
export function getLanguageQuery(event: RequestEvent): { language?: Locale } {
    const language = getExplicitLanguage(event);
    return language === undefined ? {} : { language };
}

/**
 * @brief Adds the headers to the response of a page that shows content in one language.
 * The `Vary` header tells caches that the language depends on the `Accept-Language` header and on the cookies.
 * A cache then does not send a page that was made for one visitor to a visitor with a different request.
 *
 * @param event the request event of the page
 * @param isPrivate if true, the response also gets `Cache-Control: private`. Then only the browser of the visitor
 * may store the page. A shared cache, for example a proxy, must not store it.
 */
export function setLanguageHeaders(event: RequestEvent, isPrivate: boolean): void {
    event.setHeaders({
        vary: 'Accept-Language, Cookie',
        ...(isPrivate ? { 'cache-control': 'private' } : {})
    });
}
