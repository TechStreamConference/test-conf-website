import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import InputStory from './fixtures/InputCheckboxStory.svelte';

const meta = {
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

export default meta;

type Story = StoryObj<typeof meta>;

export const Checkbox: Story = {};
