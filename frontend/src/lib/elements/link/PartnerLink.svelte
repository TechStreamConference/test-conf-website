<script lang="ts">
    import type { HTMLAnchorAttributes } from 'svelte/elements';

    import { DEFAULT_LINK_TARGET } from '$lib/helper/link-options';
    import Link from '$lib/elements/link/Link.svelte';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';

    /**
     * @brief The icons of a partner. At least one is required, a missing one is replaced by the other.
     * The values are local paths (e.g. `/img/logo_big.png`) or links provided by the backend.
     */
    type Icons =
        { iconLight: string; iconDark?: string } | { iconLight?: string; iconDark: string };

    type Props = Omit<HTMLAnchorAttributes, 'href' | 'aria-label' | 'target'> &
        Icons & {
            href: string;
            alias: string; // The name of the partner. Used as name of the link.
            copyright?: string; // The copyright text shown below the icon. May be empty or omitted.
            target?: LinkTarget;
        };

    const {
        href,
        alias,
        copyright,
        iconLight,
        iconDark,
        target = DEFAULT_LINK_TARGET,
        ...rest
    }: Props = $props();

    // At least one icon is guaranteed by the type, so the fallback is always set.
    const lightSource: string = $derived(iconLight ?? iconDark ?? '');
    const darkSource: string = $derived(iconDark ?? iconLight ?? '');
    const hasTwoIcons: boolean = $derived(lightSource !== darkSource);
</script>

<figure>
    <Link {...rest} {href} {target} aria-label={alias} variant={LinkVariant.Plain}>
        <!-- The link is named by the alias, so the icons are decorative. -->
        {#if hasTwoIcons}
            <img class:light={true} src={lightSource} alt="" />
            <img class:dark={true} src={darkSource} alt="" />
        {:else}
            <img src={lightSource} alt="" />
        {/if}
    </Link>
    {#if copyright}
        <figcaption>{copyright}</figcaption>
    {/if}
</figure>

<style>
    figure {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.5rem;

        margin: 0;
    }

    img {
        max-width: 100%;
        max-height: 6rem;

        transition: transform var(--transition-duration);
    }
    /* A small zoom of the icon only, softer than the lift of the normal link hover. */
    :global(a:hover) img,
    :global(a:focus-visible) img {
        transform: scale(1.05);
    }
    @media (prefers-reduced-motion: reduce) {
        img {
            transition: none;
        }
        :global(a:hover) img,
        :global(a:focus-visible) img {
            transform: none;
        }
    }

    figcaption {
        font-size: 0.8rem;
        text-align: center;
    }

    /* Theme switching: 'light-theme' / 'dark-theme' on the root are set by '$lib/helper/light-dark.ts'. */
    /* Without one of them the browser preference decides. */
    img.dark {
        display: none;
    }
    :global(:root.dark-theme) img.light {
        display: none;
    }
    :global(:root.dark-theme) img.dark {
        display: inline;
    }
    @media (prefers-color-scheme: dark) {
        :global(:root:not(.light-theme)) img.light {
            display: none;
        }
        :global(:root:not(.light-theme)) img.dark {
            display: inline;
        }
    }
</style>
