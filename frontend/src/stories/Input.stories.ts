import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import InputStory from './fixtures/InputStory.svelte';

const meta = {
	title: 'Components/Input',
	component: InputStory,
	args: {
		count: 1,
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
export const MultiLine: Story = {
	args: {
		count: 10
	}
};

export const Area: Story = {
	args: {
		variant: 'area',
		label: 'Area'
	}
};

export const MultiArea: Story = {
	args: {
		variant: 'area',
		label: 'Area',
		count: 10
	}
};

export const Mixed: Story = {
	args: {
		variant: 'mixed',
		label: 'Mixed'
	}
};

export const MultipleMixed: Story = {
	args: {
		variant: 'mixed',
		label: 'Mixed',
		count: 10
	}
};
