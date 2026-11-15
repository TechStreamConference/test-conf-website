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

// `isLanguageFallback` is not a prop (see `LanguageSelect.svelte`): it is read from `page.data`, so this
// story mocks it via SvelteKit's Storybook state instead of an arg.
export const LanguageFallback: Story = {
    parameters: {
        sveltekit_experimental: {
            state: {
                page: {
                    data: { isLanguageFallback: true }
                }
            }
        }
    }
};
