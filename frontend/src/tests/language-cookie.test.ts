import type { Cookies } from '@sveltejs/kit';
import type { RequestEvent } from '@sveltejs/kit';

import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { vi } from 'vitest';

import { getExplicitLanguage } from '$bff/content-language';
import { setLanguageHeaders } from '$bff/content-language';

import { LANGUAGE_COOKIE_NAME } from '$lib/helper/language-cookie.server';
import { getLanguageCookie } from '$lib/helper/language-cookie.server';
import { setLanguageCookie } from '$lib/helper/language-cookie.server';

const SESSION_COOKIE_NAME = '__Host-session';

function createCookies(values: Record<string, string> = {}): Cookies {
    return {
        get: (name: string) => values[name],
        set: vi.fn()
    } as unknown as Cookies;
}

function createRequestEvent(cookies: Cookies): RequestEvent {
    return { cookies, setHeaders: vi.fn() } as unknown as RequestEvent;
}

describe('getLanguageCookie', () => {
    it('returns the chosen UI language', () => {
        expect(getLanguageCookie(createCookies({ [LANGUAGE_COOKIE_NAME]: 'de' }))).toBe('de');
        expect(getLanguageCookie(createCookies({ [LANGUAGE_COOKIE_NAME]: 'en' }))).toBe('en');
    });

    it('returns nothing without a cookie', () => {
        expect(getLanguageCookie(createCookies())).toBeUndefined();
    });

    it('ignores a value that is not a UI language', () => {
        for (const value of ['fr', 'DE', 'de-DE', '', '"><script>']) {
            expect(
                getLanguageCookie(createCookies({ [LANGUAGE_COOKIE_NAME]: value }))
            ).toBeUndefined();
        }
    });
});

describe('setLanguageCookie', () => {
    it('stores the language in a long-lived cookie for the whole site', () => {
        const cookies = createCookies();

        setLanguageCookie(cookies, 'de');

        expect(cookies.set).toHaveBeenCalledExactlyOnceWith(LANGUAGE_COOKIE_NAME, 'de', {
            path: '/',
            maxAge: 60 * 60 * 24 * 365,
            httpOnly: true,
            sameSite: 'lax'
        });
    });

    it('refuses a language that is not a UI language', () => {
        for (const value of ['fr', 'DE', 'de-DE', '', '"><script>']) {
            const cookies = createCookies();

            expect(() => {
                setLanguageCookie(cookies, value);
            }).toThrow('is not a UI language');
            expect(cookies.set).not.toHaveBeenCalled();
        }
    });
});

describe('getExplicitLanguage', () => {
    it('returns the chosen language of a logged-out visitor', () => {
        const event = createRequestEvent(createCookies({ [LANGUAGE_COOKIE_NAME]: 'de' }));

        expect(getExplicitLanguage(event)).toBe('de');
    });

    it('returns nothing without a choice', () => {
        expect(getExplicitLanguage(createRequestEvent(createCookies()))).toBeUndefined();
    });

    it('returns nothing while a session exists, because the backend stores the language then', () => {
        const event = createRequestEvent(
            createCookies({ [LANGUAGE_COOKIE_NAME]: 'de', [SESSION_COOKIE_NAME]: 'token' })
        );

        expect(getExplicitLanguage(event)).toBeUndefined();
    });
});

describe('setLanguageHeaders', () => {
    it('tells caches that the page depends on the Accept-Language header and the cookies', () => {
        const event = createRequestEvent(createCookies());

        setLanguageHeaders(event, false);

        expect(event.setHeaders).toHaveBeenCalledExactlyOnceWith({
            vary: 'Accept-Language, Cookie'
        });
    });

    it('forbids shared caches to store the page if the cookies decided its language', () => {
        const event = createRequestEvent(createCookies());

        setLanguageHeaders(event, true);

        expect(event.setHeaders).toHaveBeenCalledExactlyOnceWith({
            vary: 'Accept-Language, Cookie',
            'cache-control': 'private'
        });
    });
});
