import type { Menu } from '$lib/helper/menus';

// See https://svelte.dev/docs/kit/types#app.d.ts
// for information about these interfaces
declare global {
    namespace App {
        // interface Error {}
        // interface Locals {}
        interface PageData {
            headerMenu?: Menu;
            footerMenu?: Menu;
        }
        // interface PageState {}
        // interface Platform {}
    }
}

export {};
