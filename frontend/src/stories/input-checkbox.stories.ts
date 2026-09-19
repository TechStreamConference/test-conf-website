import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import InputStory from './fixtures/InputCheckboxStory.svelte';

const META = {
    title: 'Components/Input',
    component: InputStory,
    args: {
        count: 1,
        label: 'Label',
        layout: 'horizontal'
    },
    argTypes: {
        layout: {
            control: 'inline-radio',
            options: ['horizontal', 'vertical', 'grid']
        }
    }
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Checkbox: Story = {};
