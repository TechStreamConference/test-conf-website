import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { LinkTarget } from '$lib/helper/link-options';

import PartnerLink from '$lib/elements/link/PartnerLink.svelte';

const META = {
    title: 'Components/PartnerLink',
    component: PartnerLink,
    args: {
        href: 'https://tech-stream.org',
        alias: 'Tech Stream Conference',
        copyright: '© Tech Stream Conference',
        iconLight: '/img/logo_big.png',
        iconDark: '/img/logo_small.png',
        target: LinkTarget.NewTab
    },
    argTypes: {
        iconLight: { control: 'text' },
        iconDark: { control: 'text' },
        target: {
            control: 'select',
            options: Object.values(LinkTarget)
        }
    }
} satisfies Meta<ComponentProps<typeof PartnerLink>>;

export default META;

type Story = StoryObj<typeof META>;
export const Partner: Story = {};
