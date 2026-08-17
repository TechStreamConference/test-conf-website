import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import { TagColor } from '$lib/helper/tag';
import TextStory from './fixtures/TextStory.svelte';

const meta = {
	title: 'Components/Text',
	component: TextStory,
	args: {
		variant: 'headline',
		text: 'Tech Stream Conference',
		render_line: false,
		preserve_newlines: false,
		tag_color: TagColor.Blue
	},
	argTypes: {
		variant: {
			control: 'select',
			options: ['headline', 'subheadline', 'paragraph', 'tag']
		},
		tag_color: {
			control: 'select',
			options: [TagColor.Blue, TagColor.Blue_Light],
			mapping: {
				Blue: TagColor.Blue,
				Blue_Light: TagColor.Blue_Light
			}
		}
	}
} satisfies Meta<ComponentProps<typeof TextStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Headline: Story = {
	args: {
		render_line: true
	}
};

export const SubHeadline: Story = {
	args: {
		variant: 'subheadline',
		text: 'Building reliable software together'
	}
};

export const Paragraph: Story = {
	args: {
		variant: 'paragraph',
		text: 'A conference for people who care about testing, quality, and sustainable engineering.'
	}
};

export const PreservedNewlines: Story = {
	args: {
		variant: 'paragraph',
		text: 'First line\nSecond line',
		preserve_newlines: true
	}
};

export const Tag: Story = {
	args: {
		variant: 'tag',
		text: 'Testing'
	}
};
