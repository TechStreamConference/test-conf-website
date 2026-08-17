import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import { LinkTarget } from '$lib/helper/link_options';
import InputStory from './fixtures/InputStory.svelte'

const meta = {
    title: 'Components/Input',
    component: InputStory,
    args: {
        variant: 'line',
        label: 'Line'
    },
    argTypes: {
        variant: {
            control: 'inline-radio',
            options: ['line', 'area']
        }
    }
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Line: Story = {};

export const Area: Story = {
    args: {
        variant: 'area'
    }
};
