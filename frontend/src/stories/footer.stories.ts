import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { MAIN_PAGE_FOOTER_MENU } from '$lib/helper/menus';
import FooterComponent from '$lib/elements/layout/Footer.svelte';
import { UserState } from '$lib/helper/menus';

const META = {
    title: 'Components/Layout',
    component: FooterComponent,
    parameters: {
        layout: 'fullscreen'
    },
    args: {
        languageTag: 'en',
        menu: MAIN_PAGE_FOOTER_MENU,
        userState: UserState.LoggedOut,
        events: [
            { label: '2026', url: '/year/2026' },
            { label: '2025', url: '/year/2025' },
            { label: '2024', url: '/year/2024' }
        ],
        footerText:
            'TECH STREAM CONFERENCE – online conference with talks on programming, maker culture and game development'
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
} satisfies Meta<typeof FooterComponent>;

export default META;
type Story = StoryObj<typeof META>;
export const Footer: Story = {};
