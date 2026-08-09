import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import Page from '../routes/+page.svelte';

const meta = {
	title: 'Pages/Home',
	component: Page,
	args: {
		data: {
			globals: {
				footer_text: 'Tech Stream Conference'
			}
		}
	}
} satisfies Meta<ComponentProps<typeof Page>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
