//
// Tech Stream Conference
// 2026
//
// Storybook stories for the links.
//

import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { LinkTarget } from '$lib/helper/link-options';

import LinkStory from './fixtures/LinkStory.svelte';

const META = {
    title: 'Components/Links',
    component: LinkStory,
    args: {
        variant: 'inline',
        label: 'Visit the conference website',
        href: 'https://tech-stream.org',
        'aria-label': 'Visit the Tech Stream Conference website',
        target: LinkTarget.NewTab
    },
    argTypes: {
        variant: {
            control: 'inline-radio',
            options: ['inline', 'button']
        },
        target: {
            control: 'select',
            options: Object.values(LinkTarget)
        }
    }
} satisfies Meta<ComponentProps<typeof LinkStory>>;

export default META;

type Story = StoryObj<typeof META>;
export const Inline: Story = {};
export const Button: Story = {
    args: {
        variant: 'button'
    }
};
