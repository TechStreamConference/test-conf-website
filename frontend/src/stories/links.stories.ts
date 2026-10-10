import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { LinkTarget } from '$lib/helper/link-options';

import LinkStory from './fixtures/LinkStory.svelte';

const META = {
    title: 'Components/Links',
    component: LinkStory,
    args: {
        variant: 'Inline',
        label: 'Visit the conference website',
        href: 'https://tech-stream.org',
        'aria-label': 'Visit the Tech Stream Conference website',
        target: LinkTarget.NewTab
    },
    argTypes: {
        variant: {
            control: 'select',
            options: ['Inline', 'Button', 'Menu', 'Footer', 'Plain']
        },
        target: {
            control: 'select',
            options: Object.values(LinkTarget)
        }
    }
} satisfies Meta<ComponentProps<typeof LinkStory>>;

export default META;

type Story = StoryObj<typeof META>;
export const Link: Story = {};
