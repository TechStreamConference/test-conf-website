import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ThemeSelectComponent from '$lib/elements/theme/ThemeSelect.svelte';

const meta = {
	title: 'Components/Theme',
	component: ThemeSelectComponent
} satisfies Meta<typeof ThemeSelectComponent>;

export default meta;
type Story = StoryObj<typeof meta>;
export const ThemeSelect: Story = {};
