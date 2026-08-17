import type { Meta, StoryObj } from '@storybook/sveltekit';
import type { ComponentProps } from 'svelte';

import Image from '$lib/elements/img/image.svelte';

const meta = {
	title: 'Components/Images/Image',
	component: Image,
	args: {
		src: '/img/logo_small.png',
		alt: 'Tech Stream Conference logo',
		width: '16rem'
	}
} satisfies Meta<ComponentProps<typeof Image>>;

export default meta;

type Story = StoryObj<typeof meta>;

export const Default: Story = {};
