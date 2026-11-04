import { describe } from 'vitest';
import { expect } from 'vitest';
import { it } from 'vitest';
import { render } from 'vitest-browser-svelte';

import type { ThemeColor } from '$lib/helper/theme-color';
import { SOCIAL_NETWORKS } from '$lib/helper/social-network';
import { SOCIAL_NETWORK_OPTIONS } from '$lib/helper/social-network';
import { SocialIconVariant } from '$lib/helper/social-icon-options';
import { SocialNetwork } from '$lib/helper/social-network';
import { isSocialNetwork } from '$lib/helper/social-network';
import { toCssColor } from '$lib/helper/theme-color';
import SocialIcon from '$lib/elements/link/SocialIcon.svelte';

const HREF = 'https://example.com/profile';
const ARIA_LABEL = 'Visit us on Twitch';

function renderIcon(props: { foreground?: ThemeColor; background?: ThemeColor } = {}) {
    return render(SocialIcon, {
        props: { network: SocialNetwork.Twitch, href: HREF, 'aria-label': ARIA_LABEL, ...props }
    });
}

describe('social network enum', () => {
    // These values are stored in the backend. If this test fails, a value was changed or removed.
    it('keeps the stored values of the networks', () => {
        expect(SocialNetwork.Twitch).toBe(1);
        expect(SocialNetwork.YouTube).toBe(2);
        expect(SocialNetwork.Discord).toBe(3);
        expect(SocialNetwork.GitHub).toBe(4);
        expect(SocialNetwork.Mastodon).toBe(5);
        expect(SocialNetwork.Bluesky).toBe(6);
        expect(SocialNetwork.X).toBe(7);
        expect(SocialNetwork.Instagram).toBe(8);
        expect(SocialNetwork.LinkedIn).toBe(9);
        expect(SocialNetwork.Website).toBe(10);
        expect(SocialNetwork.Download).toBe(11);
    });

    it('has a label and an icon for every network', () => {
        for (const option of SOCIAL_NETWORK_OPTIONS) {
            expect(SOCIAL_NETWORKS[option.value].label).toBe(option.label);
            expect(SOCIAL_NETWORKS[option.value].icon.path).not.toBe('');
        }
        expect(SOCIAL_NETWORK_OPTIONS).toHaveLength(11);
    });

    it('accepts only known numbers as network', () => {
        expect(isSocialNetwork(1)).toBe(true);
        expect(isSocialNetwork(11)).toBe(true);
        expect(isSocialNetwork(0)).toBe(false);
        expect(isSocialNetwork(12)).toBe(false);
    });
});

describe('social icon variant and text', () => {
    it('uses the purple and yellow look by default', async () => {
        const screen = await renderIcon();

        const area = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('span');
        expect(area?.classList.contains('purple-yellow')).toBe(true);
        expect(area?.classList.contains('black-white')).toBe(false);
    });

    it('can use the black and white look', async () => {
        const screen = await render(SocialIcon, {
            props: {
                network: SocialNetwork.Twitch,
                href: HREF,
                'aria-label': ARIA_LABEL,
                variant: SocialIconVariant.BlackWhite
            }
        });

        const area = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('span');
        expect(area?.classList.contains('black-white')).toBe(true);
        expect(area?.classList.contains('purple-yellow')).toBe(false);
    });

    it('shows no text by default', async () => {
        const screen = await renderIcon();

        const link = screen.getByRole('link', { name: ARIA_LABEL }).element();
        expect(link.textContent.trim()).toBe('');
        expect(link.querySelector('span')?.classList.contains('with-text')).toBe(false);
    });

    it('shows the optional text next to the icon', async () => {
        const screen = await render(SocialIcon, {
            props: {
                network: SocialNetwork.Twitch,
                href: HREF,
                'aria-label': ARIA_LABEL,
                text: 'Watch'
            }
        });

        await expect.element(screen.getByText('Watch')).toBeVisible();
        const link = screen.getByRole('link', { name: ARIA_LABEL }).element();
        expect(link.querySelector('span')?.classList.contains('with-text')).toBe(true);
    });
});

describe('theme color', () => {
    it('keeps a single color and turns a pair into light-dark', () => {
        expect(toCssColor(undefined)).toBeUndefined();
        expect(toCssColor('red')).toBe('red');
        expect(toCssColor({ light: 'white', dark: 'black' })).toBe('light-dark(white, black)');
    });
});

describe('social icon', () => {
    it('is a link with the given name and address', async () => {
        const screen = await renderIcon();

        const link = screen.getByRole('link', { name: ARIA_LABEL });
        await expect.element(link).toBeVisible();
        await expect.element(link).toHaveAttribute('href', HREF);
    });

    it('opens in a new tab without a referrer by default', async () => {
        const screen = await renderIcon();

        const link = screen.getByRole('link', { name: ARIA_LABEL });
        await expect.element(link).toHaveAttribute('target', '_blank');
        await expect.element(link).toHaveAttribute('rel', 'noopener noreferrer');
    });

    it('hides the drawn icon from assistive technology', async () => {
        const screen = await renderIcon();

        const svg = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('svg');
        expect(svg?.getAttribute('aria-hidden')).toBe('true');
        expect(svg?.querySelector('path')?.getAttribute('d')).toBe(
            SOCIAL_NETWORKS[SocialNetwork.Twitch].icon.path
        );
    });

    it('uses the colors of the theme when no color is given', async () => {
        const screen = await renderIcon();

        const span = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('span');
        expect(span?.style.getPropertyValue('--social-icon-foreground')).toBe('');
        expect(span?.style.getPropertyValue('--social-icon-background')).toBe('');
    });

    it('overrides foreground and background', async () => {
        const screen = await renderIcon({
            foreground: 'rgb(255, 0, 0)',
            background: 'rgb(0, 0, 255)'
        });

        const span = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('span');
        expect(span).not.toBeNull();
        const style = getComputedStyle(span as HTMLSpanElement);
        expect(style.color).toBe('rgb(255, 0, 0)');
        expect(style.backgroundColor).toBe('rgb(0, 0, 255)');
    });

    it('follows the theme when a color is given for light and dark', async () => {
        const screen = await renderIcon({
            foreground: { light: 'rgb(255, 0, 0)', dark: 'rgb(0, 255, 0)' },
            background: { light: 'rgb(0, 0, 255)', dark: 'rgb(255, 255, 0)' }
        });

        const span = screen.getByRole('link', { name: ARIA_LABEL }).element().querySelector('span');
        expect(span).not.toBeNull();
        const root = document.documentElement;
        try {
            root.style.colorScheme = 'light';
            expect(getComputedStyle(span as HTMLSpanElement).color).toBe('rgb(255, 0, 0)');
            expect(getComputedStyle(span as HTMLSpanElement).backgroundColor).toBe(
                'rgb(0, 0, 255)'
            );

            root.style.colorScheme = 'dark';
            expect(getComputedStyle(span as HTMLSpanElement).color).toBe('rgb(0, 255, 0)');
            expect(getComputedStyle(span as HTMLSpanElement).backgroundColor).toBe(
                'rgb(255, 255, 0)'
            );
        } finally {
            root.style.colorScheme = '';
        }
    });
});
