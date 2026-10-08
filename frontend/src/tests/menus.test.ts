import { expect, test } from 'vitest';

import type { Menu } from '$lib/helper/menus';
import type { MenuEntry } from '$lib/helper/menus';

import { getEntries } from '$lib/helper/menus';
import { UserState } from '$lib/helper/menus';

const PLAIN_ENTRY: MenuEntry = {
    label: () => 'plain',
    ariaLabel: () => 'plain aria',
    url: '/'
};

const USERNAME_ENTRY: MenuEntry<{ username: string }> = {
    label: (inputs: { username: string }) => inputs.username,
    ariaLabel: (inputs: { username: string }) => inputs.username,
    url: '/user'
};

const EMAIL_ENTRY: MenuEntry<{ email: string }> = {
    label: (inputs: { email: string }) => inputs.email,
    ariaLabel: (inputs: { email: string }) => inputs.email,
    url: '/mail'
};

// Note: the `@ts-expect-error` directives are verified by `svelte-check` (`just frontend-check`), not by vitest.

test('getEntries returns the entries of the given state', () => {
    const menu: Menu = {
        [UserState.LoggedOut]: [PLAIN_ENTRY],
        [UserState.LoggedIn]: []
    };
    expect(getEntries(menu, UserState.LoggedOut)).toEqual([PLAIN_ENTRY]);
    expect(getEntries(menu, UserState.LoggedIn)).toEqual([]);
});

test('an entry without placeholders fits every menu', () => {
    const menu: Menu<{ username: string }> = {
        [UserState.LoggedOut]: [PLAIN_ENTRY],
        [UserState.LoggedIn]: [PLAIN_ENTRY]
    };
    expect(getEntries(menu, UserState.LoggedIn)).toEqual([PLAIN_ENTRY]);
});

test('entries with different placeholders fit a menu with the combined placeholders', () => {
    const menu: Menu<{ username: string; email: string }> = {
        [UserState.LoggedOut]: [PLAIN_ENTRY],
        [UserState.LoggedIn]: [PLAIN_ENTRY, USERNAME_ENTRY, EMAIL_ENTRY]
    };
    expect(getEntries(menu, UserState.LoggedIn)).toHaveLength(3);
});

test('an entry with placeholders does not fit a menu without them', () => {
    const menu: Menu = {
        [UserState.LoggedOut]: [PLAIN_ENTRY],
        // @ts-expect-error The menu has no placeholders, but the entry needs a username.
        [UserState.LoggedIn]: [USERNAME_ENTRY]
    };
    expect(menu[UserState.LoggedOut]).toHaveLength(1);
});

test('an entry with a foreign placeholder does not fit the menu', () => {
    const menu: Menu<{ username: string }> = {
        [UserState.LoggedOut]: [],
        // @ts-expect-error The menu provides a username, but the entry needs an email.
        [UserState.LoggedIn]: [EMAIL_ENTRY]
    };
    expect(menu[UserState.LoggedIn]).toHaveLength(1);
});

test('a menu must define every state', () => {
    // @ts-expect-error The state `LoggedIn` is missing.
    const menu: Menu = {
        [UserState.LoggedOut]: [PLAIN_ENTRY]
    };
    expect(menu[UserState.LoggedOut]).toHaveLength(1);
});
