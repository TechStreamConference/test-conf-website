import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import LogosStory from './fixtures/LogosStory.svelte';

const meta = {
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

export default meta;
type Story = StoryObj<typeof meta>;
export const Big: Story = {};
export const Small: Story = {
	args: {
		variant: 'small',
		width: '8rem'
	}
};
