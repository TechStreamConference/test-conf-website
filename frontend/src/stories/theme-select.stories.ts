import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ThemeSelectStory from './fixtures/ThemeSelectStory.svelte';

const META = {
    title: 'Components/Theme',
    component: ThemeSelectStory,
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
} satisfies Meta<ComponentProps<typeof ThemeSelectStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const ThemeSelect: Story = {};
