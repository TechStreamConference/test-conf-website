import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import ShowcaseStory from './fixtures/ShowcaseStory.svelte';

const meta = {
	title: 'Pages/Home',
	component: ShowcaseStory
} satisfies Meta<ComponentProps<typeof ShowcaseStory>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
