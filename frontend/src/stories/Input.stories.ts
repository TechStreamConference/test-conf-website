import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import InputStory from './fixtures/InputStory.svelte';

const meta = {
	title: 'Components/Input',
	component: InputStory,
	args: {
		count: 1,
		variant: 'line',
		label: 'Label',
		layout: 'vertical'
	},
	argTypes: {
		variant: {
			control: 'inline-radio',
			options: ['line', 'area', 'mixed']
		},
		layout: {
			control: 'inline-radio',
			options: ['horizontal', 'vertical', 'grid']
		}
	}
} satisfies Meta<ComponentProps<typeof InputStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Line_Area: Story = {};
