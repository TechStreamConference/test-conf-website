import type { Meta, StoryObj } from '@storybook/sveltekit';

import ThemeSelectComponent from '$lib/elements/theme/theme_select.svelte';

const meta = {
	title: 'Components/Theme',
	component: ThemeSelectComponent
} satisfies Meta<typeof ThemeSelectComponent>;

export default meta;

type Story = StoryObj<typeof meta>;

export const ThemeSelect: Story = {};
