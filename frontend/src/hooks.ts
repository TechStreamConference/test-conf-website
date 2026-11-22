import type { Reroute } from '@sveltejs/kit';

import { stripLanguagePrefix } from '$lib/helper/language-url';

/**
 * @brief Routes a language-prefixed path (e.g. `/de/imprint`) as if it were the path without the prefix
 * (`/imprint`). There is no `[lang]` route segment; the browser still shows the prefixed URL.
 * @param url the requested URL.
 * @returns the path to route to, or undefined to route the original path unchanged.
 */
export const reroute: Reroute = ({ url }) => {
    const { languageCode, rest } = stripLanguagePrefix(url.pathname);
    if (languageCode === undefined) {
        return undefined;
    }
    return rest === '' ? '/' : `/${rest}`;
};
