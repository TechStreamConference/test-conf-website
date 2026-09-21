//
// Tech Stream Conference
// 2026
//
// Storybook stories for the range input.
//

import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import InputStory from './fixtures/InputRangeStory.svelte';

const META = {
    title: 'Components/Input',
    component: InputStory,
    args: {
        count: 1,
        label: 'Label',
        layout: 'horizontal',
        min: 0,
        max: 100,
        step: 1
    },
    argTypes: {
        layout: {
            control: 'inline-radio',
            options: ['horizontal', 'vertical', 'grid']
        },
        min: {
            control: 'number'
        },
        max: {
            control: 'number'
        },
        step: {
            control: 'number'
        }
    }
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default META;

type Story = StoryObj<typeof META>;

export const Range: Story = {};
