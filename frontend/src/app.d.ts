import type { LanguageTag } from '$lib/helper/language';
import type { Menu } from '$lib/helper/menus';

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        interface Locals {
            languageTag?: string;
            // The language found in the URL path (e.g. `de` for `/de/imprint`), stripped by `reroute` in
            // `hooks.ts`. Any ISO 639 code, not only one of this site's UI languages. Only valid for the
            // current request, not persisted. `handle` always sets this, so it is not optional itself;
            // its value is `undefined` when the path has no language prefix.
            urlLanguageTag: string | undefined;
        }
        interface PageData {
            languageTag?: LanguageTag;
            headerMenu?: Menu;
            footerMenu?: Menu;
        }
        // interface PageState {}
        // interface Platform {}
    }
}

export {};
