import { error } from '@sveltejs/kit';

import type { Locale } from '$paraglide/runtime';
import { isLocale } from '$paraglide/runtime';

import { setLanguageCookie } from '$lib/helper/language-cookie.server';

import type { RequestHandler } from './$types';

interface ChooseLanguageBody {
    language: string;
}

/**
 * @brief Stores the UI language that the visitor explicitly chose.
 * @throws HttpError with status 400 if the body does not contain a valid UI language.
 */
export const PUT: RequestHandler = async (event) => {
    const body = (await event.request.json()) as ChooseLanguageBody;
    if (!isLocale(body.language)) {
        error(400, `"${body.language}" is not a UI language.`);
    }

    const language: Locale = body.language;
    setLanguageCookie(event.cookies, language);
    return new Response(null, { status: 204 });
};
