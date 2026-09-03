import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import ImageComponent from '$lib/elements/img/Image.svelte';

const meta = {
	title: 'Components/Images/Image',
	component: ImageComponent,
	args: {
		src: '/img/logo_small.png',
		alt: 'Tech Stream Conference logo',
		width: '16rem'
	}
} satisfies Meta<ComponentProps<typeof ImageComponent>>;

export default meta;
type Story = StoryObj<typeof meta>;
export const Image: Story = {};
