import type { LanguageTag } from '$lib/helper/language';
import type { Menu } from '$lib/helper/menus';

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        interface Locals {
            languageTag: string;
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
