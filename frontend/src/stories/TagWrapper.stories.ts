import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import TagWrapperComponent from '$lib/elements/text/tag_wrapper.svelte';

const meta = {
	title: 'Components/Text',
	component: TagWrapperComponent,
	args: {
		tags: [
			{ id: 1, color_id: 1, text: 'Testing' },
			{ id: 2, color_id: 2, text: 'Frontend' },
			{ id: 3, color_id: 1, text: 'Svelte' }
		]
	}
} satisfies Meta<ComponentProps<typeof TagWrapperComponent>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const TagWrapper: Story = {};
