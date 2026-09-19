import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import InputStory from './fixtures/InputRangeStory.svelte';

const meta = {
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

export default meta;

type Story = StoryObj<typeof meta>;

export const Range: Story = {};
