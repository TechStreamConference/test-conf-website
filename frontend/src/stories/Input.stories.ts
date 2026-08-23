import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import InputStory from './fixtures/InputStory.svelte';

const meta = {
	title: 'Components/Input',
	component: InputStory,
	args: {
		count: 1,
		variant: 'line',
		label: 'Label'
	},
	argTypes: {
		variant: {
			control: 'inline-radio',
			options: ['line', 'area', 'mixed']
		}
	}
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Line_Area: Story = {};
