import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import LanguageSelectStory from './fixtures/LanguageSelectStory.svelte';

const META = {
    title: 'Components/Select',
    component: LanguageSelectStory,
    parameters: {
        layout: 'fullscreen'
    },
    args: {
        languageTag: 'en'
    },
    argTypes: {
        languageTag: {
            control: 'select',
            options: ['en', 'de']
        }
    }
} satisfies Meta<ComponentProps<typeof LanguageSelectStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Language: Story = {};
