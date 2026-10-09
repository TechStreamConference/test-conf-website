import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { MAIN_PAGE_FOOTER_MENU } from '$lib/helper/menus';
import { MAIN_PAGE_HEADER_MENU } from '$lib/helper/menus';
import { UserState } from '$lib/helper/menus';

import BasePageStory from './fixtures/BasePageStory.svelte';

const META = {
    title: 'Components/Layout',
    component: BasePageStory,
    parameters: {
        layout: 'fullscreen'
    },
    args: {
        languageTag: 'en',
        userState: UserState.LoggedOut,
        headerMenu: MAIN_PAGE_HEADER_MENU,
        footerMenu: MAIN_PAGE_FOOTER_MENU,
        events: [
            { label: '2026', url: '/year/2026' },
            { label: '2025', url: '/year/2025' },
            { label: '2024', url: '/year/2024' }
        ],
        footerText:
            'TECH STREAM CONFERENCE – online conference with talks on programming, maker culture and game development',
        paragraphs: 3
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
        },
        paragraphs: {
            control: { type: 'number', min: 0, max: 200 }
        }
    }
} satisfies Meta<ComponentProps<typeof BasePageStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const BasePage: Story = {};
