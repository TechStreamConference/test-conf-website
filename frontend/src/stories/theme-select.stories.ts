import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ThemeSelectComponent from '$lib/elements/theme/ThemeSelect.svelte';

const META = {
    title: 'Components/Theme',
    component: ThemeSelectComponent
} satisfies Meta<typeof ThemeSelectComponent>;

export default META;
type Story = StoryObj<typeof META>;
export const ThemeSelect: Story = {};
