import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import { LinkTarget } from '$lib/helper/link_options';
import LinkStory from './fixtures/LinkStory.svelte';

const meta = {
	title: 'Components/Links',
	component: LinkStory,
	args: {
		variant: 'inline',
		label: 'Visit the conference website',
		href: 'https://tech-stream.org',
		aria_label: 'Visit the Tech Stream Conference website',
		target: LinkTarget.NewTab
	},
	argTypes: {
		variant: {
			control: 'inline-radio',
			options: ['inline', 'button']
		},
		target: {
			control: 'select',
			options: Object.values(LinkTarget)
		}
	}
} satisfies Meta<ComponentProps<typeof LinkStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Inline: Story = {};

export const Button: Story = {
	args: {
		variant: 'button'
	}
};
