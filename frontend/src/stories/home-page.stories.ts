//
// Tech Stream Conference
// 2026
//
// Storybook stories for the home page.
//

import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ShowcaseStory from './fixtures/ShowcaseStory.svelte';

const META = {
    title: 'Pages',
    component: ShowcaseStory
} satisfies Meta<ComponentProps<typeof ShowcaseStory>>;

export default META;
type Story = StoryObj<typeof META>;
export const Home: Story = {};
