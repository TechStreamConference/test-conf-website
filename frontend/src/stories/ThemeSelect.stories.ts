import type { Meta, StoryObj } from '@storybook/sveltekit';

import ThemeSelect from '$lib/elements/theme/theme_select.svelte';

const meta = {
	title: 'Components/Theme/Theme Select',
	component: ThemeSelect
} satisfies Meta<typeof ThemeSelect>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
