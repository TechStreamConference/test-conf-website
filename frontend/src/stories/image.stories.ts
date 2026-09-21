//
// Tech Stream Conference
// 2026
//
// Storybook stories for the image.
//

import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import ImageComponent from '$lib/elements/img/Image.svelte';

const META = {
    title: 'Components/Images/Image',
    component: ImageComponent,
    args: {
        src: '/img/logo_small.png',
        alt: 'Tech Stream Conference logo',
        width: '16rem'
    }
} satisfies Meta<ComponentProps<typeof ImageComponent>>;

export default META;
type Story = StoryObj<typeof META>;
export const Image: Story = {};
