import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ButtonStory from './fixtures/ButtonStory.svelte';

const META = {
    title: 'Components/Input',
    component: ButtonStory,
    args: {
        label: 'Click me',
        'aria-label': 'Click me',
        type: 'button',
        disabled: false
    },
    argTypes: {
        type: {
            control: 'inline-radio',
            options: ['button', 'submit', 'reset']
        }
    }
} satisfies Meta<ComponentProps<typeof ButtonStory>>;

export default META;

type Story = StoryObj<typeof META>;
export const Button: Story = {};
