<script lang="ts">
    import type { HTMLAnchorAttributes } from 'svelte/elements';
    import type { Snippet } from 'svelte';

    import { DEFAULT_LINK_TARGET } from '$lib/helper/link-options';
    import { getRel } from '$lib/helper/link-options';
    import { LinkTarget } from '$lib/helper/link-options';
    import { LinkVariant } from '$lib/helper/link-options';
    import '$lib/styles/hover.css';

    interface Props extends Omit<HTMLAnchorAttributes, 'href' | 'aria-label' | 'target'> {
        children: Snippet;
        href: string;
        'aria-label': string;
        target?: LinkTarget;
        variant?: LinkVariant;
    }
    const {
        children,
        href,
        'aria-label': ariaLabel,
        target = DEFAULT_LINK_TARGET,
        variant = LinkVariant.Button,
        rel: relName,
        ...rest
    }: Props = $props();
</script>

<!-- eslint-disable svelte/no-navigation-without-resolve -->
<a
    {...rest}
    class:hover-lift={true}
    class:menu={variant === LinkVariant.Menu || variant === LinkVariant.Footer}
    class:footer={variant === LinkVariant.Footer}
    class:plain={variant === LinkVariant.Plain}
    {href}
    {target}
    aria-label={ariaLabel}
    rel={getRel(target, relName)}
>
    {@render children()}
</a>

<!-- eslint-enable svelte/no-navigation-without-resolve -->

<style>
    a {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 0.5rem;

        padding: 1rem 2rem;
        min-height: 4.4rem;
        border-radius: var(--border-radius);
        border: none;

        background-color: var(--primary-color-400);
        color: var(--white-color);
        text-decoration: none;
        cursor: pointer;
    }
    /* The rising and the shadow of the hover effect are in 'src/lib/styles/hover.css' (class 'hover-lift'). */
    a:hover,
    a:focus-visible {
        background-color: var(--primary-color-600);

        outline: none;
    }

    /* Menu variant: a plain link without the button look, used on the colored header. */
    a.menu {
        display: flex;
        justify-content: flex-start;

        min-height: 3rem;
        padding: 0 1rem;

        background-color: transparent;
        box-shadow: none;
    }
    /* Footer variant: a compact menu link with centered content, so many entries stay small. */
    a.menu.footer {
        justify-content: center;

        min-height: 2.25rem;
        padding: 0 0.75rem;
    }
    a.menu:hover,
    a.menu:focus-visible {
        background-color: var(--primary-color-400);

        box-shadow: none;
        transform: none;
    }
    a.menu:focus-visible {
        outline: 0.2rem solid var(--white-color);
        outline-offset: -0.2rem;
    }

    /* Plain variant: only the content, without padding, background or hover effect, e.g. for a logo. */
    a.plain {
        padding: 0;

        background-color: transparent;
        box-shadow: none;
    }
    a.plain:hover,
    a.plain:focus-visible {
        background-color: transparent;

        box-shadow: none;
        transform: none;
    }
    a.plain:focus-visible {
        outline: 0.2rem solid var(--white-color);
        outline-offset: 0.2rem;
    }
</style>
