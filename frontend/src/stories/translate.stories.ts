import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import TranslateStory from './fixtures/TranslateStory.svelte';

const META = {
    title: 'Helper/Translate',
    component: TranslateStory,
    args: {
        message: 'global_themeSelectDark',
        languageTag: 'de',
        year: '2026'
    },
    argTypes: {
        message: {
            control: 'select',
            options: ['global_themeSelectDark', 'global_themeSelectLight', 'footer_copyright']
        },
        languageTag: {
            control: 'select',
            options: ['de', 'en', 'DE', 'en-US', 'en-GB', 'fr']
        },
        year: {
            control: 'text'
        }
    }
} satisfies Meta<ComponentProps<typeof TranslateStory>>;

export default META;

type Story = StoryObj<typeof META>;
export const I18N: Story = {};
