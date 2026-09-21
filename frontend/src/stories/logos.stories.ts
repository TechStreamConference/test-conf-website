//
// Tech Stream Conference
// 2026
//
// Storybook stories for the logos.
//

import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import LogosStory from './fixtures/LogosStory.svelte';

const META = {
    title: 'Components/Images/Logos',
    component: LogosStory,
    args: {
        variant: 'big',
        width: '24rem'
    },
    argTypes: {
        variant: {
            control: 'inline-radio',
            options: ['big', 'small']
        }
    }
} satisfies Meta<ComponentProps<typeof LogosStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Big: Story = {};
export const Small: Story = {
    args: {
        variant: 'small',
        width: '8rem'
    }
};
