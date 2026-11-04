import type { ComponentProps } from 'svelte';
import type { Meta } from '@storybook/sveltekit';
import type { StoryObj } from '@storybook/sveltekit';

import { LinkTarget } from '$lib/helper/link-options';
import { SOCIAL_NETWORK_OPTIONS } from '$lib/helper/social-network';
import { SocialIconVariant } from '$lib/helper/social-icon-options';
import { SocialNetwork } from '$lib/helper/social-network';
import SocialIcon from '$lib/elements/link/SocialIcon.svelte';

const VARIANT_VALUES = Object.values(SocialIconVariant).filter(
    (value): value is SocialIconVariant => typeof value === 'number'
);

const META = {
    title: 'Components/SocialIcon',
    component: SocialIcon,
    args: {
        network: SocialNetwork.Twitch,
        href: 'https://www.twitch.tv',
        'aria-label': 'Visit us on Twitch',
        target: LinkTarget.NewTab,
        variant: SocialIconVariant.PurpleYellow
    },
    argTypes: {
        network: {
            control: 'select',
            options: SOCIAL_NETWORK_OPTIONS.map((option) => option.value),
            labels: Object.fromEntries(
                SOCIAL_NETWORK_OPTIONS.map((option) => [option.value, option.label])
            )
        },
        target: {
            control: 'select',
            options: Object.values(LinkTarget)
        },
        variant: {
            control: 'radio',
            options: VARIANT_VALUES,
            labels: Object.fromEntries(
                VARIANT_VALUES.map((value) => [value, SocialIconVariant[value]])
            )
        },
        text: { control: 'text' },
        // A single color string, or an object like { "light": "#fff", "dark": "#000" } for one color per theme.
        foreground: { control: 'object' },
        background: { control: 'object' }
    }
} satisfies Meta<ComponentProps<typeof SocialIcon>>;

export default META;

type Story = StoryObj<typeof META>;
export const Icon: Story = {};
