import type { Inputs } from '$lib/helper/translate';
import type { Message } from '$lib/helper/translate';
import type { NoInputs } from '$lib/helper/translate';

import { m } from '$paraglide/messages';

export enum UserState {
    LoggedOut,
    LoggedIn
}

/**
 * @brief A single link of a menu. Does not know in which state of the user it is shown.
 * The texts are message functions, so the caller translates them with `i18n` and supplies the placeholder values.
 *
 * @see i18n
 */
export interface MenuEntry<TInputs extends Inputs = NoInputs> {
    label: Message<TInputs>;
    ariaLabel: Message<TInputs>;
    url: string;
}

/**
 * @brief The entries of a menu for every state of the user.
 * `TInputs` is the combined set of placeholders of all entries. An entry may need fewer, but not other placeholders.
 */
export type Menu<TInputs extends Inputs = NoInputs> = Record<UserState, MenuEntry<TInputs>[]>;

//#region MenuEntries

const HOMEPAGE_ENTRY: MenuEntry = {
    label: m.menu_homepage,
    ariaLabel: m.menu_homepage_aria,
    url: '/'
};

//#endregion

//#region Menus

export const MAIN_MENU: Menu = {
    [UserState.LoggedOut]: [HOMEPAGE_ENTRY],
    [UserState.LoggedIn]: [HOMEPAGE_ENTRY]
};

//#endregion

export function getEntries<TInputs extends Inputs>(
    menu: Menu<TInputs>,
    userState: UserState
): MenuEntry<TInputs>[] {
    return menu[userState];
}
