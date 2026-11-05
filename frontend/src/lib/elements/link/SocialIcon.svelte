<script lang="ts">
    import type { HTMLAnchorAttributes } from 'svelte/elements';

    import type { ThemeColor } from '$lib/helper/theme-color';
    import { DEFAULT_LINK_TARGET } from '$lib/helper/link-options';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';
    import { SOCIAL_NETWORKS } from '$lib/helper/social-network';
    import { SocialIconVariant } from '$lib/helper/social-icon-options';
    import { SocialNetwork } from '$lib/helper/social-network';
    import { toCssColor } from '$lib/helper/theme-color';
    import Link from '$lib/elements/link/Link.svelte';
    import '$lib/styles/hover.css';

    interface Props extends Omit<HTMLAnchorAttributes, 'href' | 'aria-label' | 'target'> {
        network: SocialNetwork;
        href: string;
        'aria-label': string;
        target?: LinkTarget;
        variant?: SocialIconVariant;
        text?: string;
        foreground?: ThemeColor;
        background?: ThemeColor;
    }
    const {
        network,
        href,
        'aria-label': ariaLabel,
        target = DEFAULT_LINK_TARGET,
        variant = SocialIconVariant.PurpleYellow,
        text,
        foreground,
        background,
        ...rest
    }: Props = $props();

    const icon = $derived(SOCIAL_NETWORKS[network].icon);
    const hasText = $derived(Boolean(text));
</script>

<Link {...rest} {href} aria-label={ariaLabel} {target} variant={LinkVariant.Plain}>
    <span
        class:social-icon={true}
        class:hover-lift={true}
        class:black-white={variant === SocialIconVariant.BlackWhite}
        class:purple-yellow={variant === SocialIconVariant.PurpleYellow}
        class:with-text={hasText}
        style:--social-icon-foreground={toCssColor(foreground)}
        style:--social-icon-background={toCssColor(background)}
    >
        <svg viewBox="0 0 {icon.width} {icon.height}" aria-hidden="true" focusable="false">
            <path d={icon.path} />
        </svg>
        {#if hasText}
            <span>{text}</span>
        {/if}
    </span>
</Link>

<style>
    /*
     * The default colors of the variants. `foreground` and `background` override them:
     * `foreground` colors the icon and the text, `background` the area.
     */
    .black-white {
        --social-icon-default-icon: var(--text-color);
        --social-icon-default-text: var(--text-color);
        --social-icon-default-background: transparent;
        --social-icon-default-hover-background: transparent;

        /* Without an area, there is nothing a shadow could belong to. The icon only rises. */
        --hover-lift-shadow: none;
        --hover-lift-shadow-raised: none;
        --hover-lift-shadow-pressed: none;
    }
    .purple-yellow {
        --social-icon-default-icon: var(--secondary-color);
        --social-icon-default-text: var(--white-color);
        --social-icon-default-background: var(--primary-color-400);
        --social-icon-default-hover-background: var(--primary-color-600);
    }

    .social-icon {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.75rem;

        min-width: var(--social-icon-size, 4.4rem);
        height: var(--social-icon-size, 4.4rem);
        border-radius: var(--border-radius);

        background-color: var(--social-icon-background, var(--social-icon-default-background));
        color: var(--social-icon-foreground, var(--social-icon-default-text));
    }
    /* The link has the hover and the focus. The rising and the shadow come from 'src/lib/styles/hover.css'. */
    :global(a:is(:hover, :focus-visible)) > .social-icon {
        background-color: var(
            --social-icon-background,
            var(--social-icon-default-hover-background)
        );
    }
    .social-icon.with-text {
        padding: 0 1.5rem;
    }

    svg {
        flex-shrink: 0;
        width: calc(var(--social-icon-size, 4.4rem) * 0.7);
        height: calc(var(--social-icon-size, 4.4rem) * 0.7);

        fill: var(--social-icon-foreground, var(--social-icon-default-icon));
    }
    .with-text svg {
        width: 2.4rem;
        height: 2.4rem;
    }
    .with-text span {
        font-size: 1.5rem;
    }
</style>
