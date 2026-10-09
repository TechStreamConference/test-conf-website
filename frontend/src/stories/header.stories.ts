import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { MAIN_MENU } from '$lib/helper/menus';
import HeaderComponent from '$lib/elements/layout/Header.svelte';
import { UserState } from '$lib/helper/menus';

const META = {
    title: 'Components/Layout',
    component: HeaderComponent,
    parameters: {
        layout: 'fullscreen'
    },
    args: {
        languageTag: 'en',
        menu: MAIN_MENU,
        userState: UserState.LoggedOut,
        currentPath: '/'
    },
    argTypes: {
        languageTag: {
            control: 'select',
            options: ['en', 'de']
        },
        userState: {
            control: 'radio',
            options: ['LoggedOut', 'LoggedIn'],
            mapping: {
                LoggedOut: UserState.LoggedOut,
                LoggedIn: UserState.LoggedIn
            }
        }
    }
} satisfies Meta<typeof HeaderComponent>;

export default META;
type Story = StoryObj<typeof META>;
export const Header: Story = {};
