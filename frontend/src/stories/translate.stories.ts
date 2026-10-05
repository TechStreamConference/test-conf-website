import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import TranslateStory from './fixtures/TranslateStory.svelte';

const META = {
    title: 'Helper/Translate',
    component: TranslateStory,
    args: {
        message: 'test_plain',
        languageTag: 'de',
        placeholder1: 'Placeholder 1',
        placeholder2: 'Placeholder 2'
    },
    argTypes: {
        message: {
            control: 'select',
            options: ['test_plain', 'test_plain2', 'test_withPlaceholder']
        },
        languageTag: {
            control: 'select',
            options: ['de', 'en', 'DE', 'en-US', 'en-GB', 'fr']
        },
        placeholder1: {
            control: 'text'
        },
        placeholder2: {
            control: 'text'
        }
    }
} satisfies Meta<ComponentProps<typeof TranslateStory>>;

export default META;

type Story = StoryObj<typeof META>;
export const I18N: Story = {};
