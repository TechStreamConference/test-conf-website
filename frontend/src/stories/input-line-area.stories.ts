import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { InputType } from '$lib/helper/input';

import InputStory from './fixtures/InputLineAreaStory.svelte';

const META = {
    title: 'Components/Input',
    component: InputStory,
    args: {
        count: 1,
        variant: 'line',
        label: 'Label',
        layout: 'vertical',
        type: InputType.Text,
        maxlength: undefined,
        step: undefined
    },
    argTypes: {
        variant: {
            control: 'inline-radio',
            options: ['line', 'area', 'mixed']
        },
        layout: {
            control: 'inline-radio',
            options: ['horizontal', 'vertical', 'grid']
        },
        type: {
            control: 'select',
            options: Object.values(InputType)
        },
        maxlength: {
            control: 'number',
            step: 1,
            defaultValue: undefined
        },
        step: {
            control: 'number',
            step: 1,
            description: 'In minutes for `time` and `datetime-local`, as in HTML for all others.',
            defaultValue: undefined
        }
    }
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Line_Area: Story = {};
